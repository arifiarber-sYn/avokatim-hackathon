import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.matters import get_owned_matter
from app.database import get_db
from app.deps import get_current_user
from app.models import Document, User
from app.schemas.documents import DocumentOut, ReviewDecisionIn, ReviewRequestIn
from app.services import rag, storage
from app.services.audit import log_action

router = APIRouter(tags=["documents"])

MAX_UPLOAD_BYTES = 100 * 1024 * 1024


def _to_out(doc: Document) -> DocumentOut:
    out = DocumentOut.model_validate(doc)
    out.has_text = bool(doc.text_content)
    return out


@router.get("/matters/{matter_id}/documents", response_model=list[DocumentOut])
async def list_documents(
    matter_id: uuid.UUID,
    include_versions: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_owned_matter(db, user, matter_id)
    stmt = select(Document).where(Document.matter_id == matter_id)
    if not include_versions:
        stmt = stmt.where(Document.is_latest.is_(True))
    stmt = stmt.order_by(Document.created_at.desc())
    return [_to_out(d) for d in (await db.execute(stmt)).scalars()]


@router.post(
    "/matters/{matter_id}/documents",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    matter_id: uuid.UUID,
    file: UploadFile = File(...),
    category: str | None = Form(None),
    replaces_family_id: uuid.UUID | None = Form(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a file. Pass replaces_family_id to add a new version of an
    existing document. Text is extracted (OCR for scans) and indexed for
    search and AI analysis."""
    await get_owned_matter(db, user, matter_id)
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File too large")
    if not content:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty file")

    version = 1
    family_id = uuid.uuid4()
    if replaces_family_id:
        prev = (
            await db.execute(
                select(Document).where(
                    Document.family_id == replaces_family_id,
                    Document.is_latest.is_(True),
                    Document.tenant_id == user.tenant_id,
                )
            )
        ).scalar_one_or_none()
        if prev is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Previous version not found")
        prev.is_latest = False
        family_id = prev.family_id
        version = prev.version + 1

    rel_path, sha, encrypted = storage.save_file(content, user.tenant_id)
    mime = file.content_type or "application/octet-stream"
    text, ocr_status = storage.extract_text(content, mime, file.filename or "file")

    doc = Document(
        tenant_id=user.tenant_id,
        matter_id=matter_id,
        family_id=family_id,
        version=version,
        is_latest=True,
        filename=file.filename or "file",
        mime_type=mime,
        size_bytes=len(content),
        sha256=sha,
        storage_path=rel_path,
        encrypted=encrypted,
        category=category,
        uploaded_by_id=user.id,
        text_content=text or None,
        ocr_status=ocr_status,
    )
    db.add(doc)
    await db.flush()
    if text:
        await rag.index_document_chunks(db, doc)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="document.upload",
        entity_type="document", entity_id=str(doc.id),
        details={"filename": doc.filename, "version": version},
    )
    await db.commit()
    await db.refresh(doc)
    return _to_out(doc)


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await db.get(Document, document_id)
    if doc is None or doc.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    content = storage.load_file(doc.storage_path, doc.encrypted)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="document.download",
        entity_type="document", entity_id=str(doc.id),
    )
    await db.commit()
    return Response(
        content=content,
        media_type=doc.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{doc.filename}"'},
    )


async def _get_owned_document(
    db: AsyncSession, user: User, document_id: uuid.UUID
) -> Document:
    doc = await db.get(Document, document_id)
    if doc is None or doc.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    if doc.matter_id:
        await get_owned_matter(db, user, doc.matter_id)  # enforces restricted access
    return doc


@router.get("/documents/review-inbox", response_model=list[DocumentOut])
async def review_inbox(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Documents waiting for the current user's approval."""
    stmt = (
        select(Document)
        .where(
            Document.tenant_id == user.tenant_id,
            Document.reviewer_id == user.id,
            Document.approval_status == "in_review",
        )
        .order_by(Document.created_at.desc())
    )
    return [_to_out(d) for d in (await db.execute(stmt)).scalars()]


@router.post("/documents/{document_id}/request-review", response_model=DocumentOut)
async def request_review(
    document_id: uuid.UUID,
    body: ReviewRequestIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a draft to a colleague (typically a partner) for internal approval."""
    doc = await _get_owned_document(db, user, document_id)
    reviewer = await db.get(User, body.reviewer_id)
    if reviewer is None or reviewer.tenant_id != user.tenant_id or not reviewer.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reviewer not found")
    doc.approval_status = "in_review"
    doc.reviewer_id = reviewer.id
    doc.approval_note = None
    doc.reviewed_at = None
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="document.review_request",
        entity_type="document", entity_id=str(doc.id),
        details={"reviewer": reviewer.full_name},
    )
    await db.commit()
    await db.refresh(doc)
    return _to_out(doc)


@router.post("/documents/{document_id}/review", response_model=DocumentOut)
async def review_document(
    document_id: uuid.UUID,
    body: ReviewDecisionIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """The assigned reviewer (or an admin) approves or requests changes."""
    doc = await _get_owned_document(db, user, document_id)
    if doc.approval_status != "in_review":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Document is not awaiting review")
    if user.id != doc.reviewer_id and user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the assigned reviewer can decide")
    if body.decision not in ("approve", "request_changes"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown decision")
    doc.approval_status = "approved" if body.decision == "approve" else "changes_requested"
    doc.approval_note = body.note
    doc.reviewed_at = datetime.now(UTC)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="document.review_decision",
        entity_type="document", entity_id=str(doc.id),
        details={"decision": body.decision},
    )
    await db.commit()
    await db.refresh(doc)
    return _to_out(doc)


@router.get("/documents/{document_id}/text")
async def document_text(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await db.get(Document, document_id)
    if doc is None or doc.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return {"text": doc.text_content or "", "ocr_status": doc.ocr_status}
