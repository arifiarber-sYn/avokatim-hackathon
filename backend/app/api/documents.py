import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.matters import get_owned_matter
from app.database import get_db
from app.deps import get_current_user
from app.models import Document, User
from app.schemas.documents import DocumentOut, ReviewDecisionIn, ReviewRequestIn
from app.services import deadline_suggest, rag, storage
from app.services.audit import log_action

router = APIRouter(tags=["documents"])

MAX_UPLOAD_BYTES = 100 * 1024 * 1024

# Upload allowlist (D-033): documents, images, text and common evidence
# media — never executables or archives. The declared MIME is client-
# controlled, so the file extension is checked as well.
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.oasis.opendocument.text",
    "application/vnd.oasis.opendocument.spreadsheet",
    "application/rtf",
    "text/plain",
    "text/csv",
    "text/markdown",
    "message/rfc822",
    "application/octet-stream",  # unknown — the extension check decides
}
ALLOWED_MIME_PREFIXES = ("image/", "audio/", "video/")
ALLOWED_EXTENSIONS = {
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "odt", "ods", "rtf",
    "txt", "csv", "md", "eml",
    "jpg", "jpeg", "png", "gif", "webp", "tif", "tiff", "heic", "bmp",
    "mp3", "wav", "m4a", "ogg", "opus", "amr", "mp4", "mov", "webm", "mkv", "avi",
}


def upload_type_allowed(filename: str, content_type: str | None) -> bool:
    mime = (content_type or "application/octet-stream").split(";")[0].strip().lower()
    if mime not in ALLOWED_MIME_TYPES and not mime.startswith(ALLOWED_MIME_PREFIXES):
        return False
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in ALLOWED_EXTENSIONS


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
    if not upload_type_allowed(file.filename or "file", file.content_type):
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "File type not allowed — documents, images and audio/video only",
        )
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
    if doc.text_content and (category or "") != "draft":
        # D-043: propose deadlines from the document in the background;
        # the lawyer accepts/dismisses — nothing is auto-created.
        deadline_suggest.scan_document_background(doc.id)
    return _to_out(doc)


# ---------- Outlook add-in: save an email into a matter (D-059 F8) ----------


class EmailAttachmentIn(BaseModel):
    name: str
    content_base64: str


class ImportEmailIn(BaseModel):
    subject: str = ""
    sender: str = ""
    received_at: str = ""
    body: str = ""
    attachments: list[EmailAttachmentIn] = []


@router.post("/matters/{matter_id}/import-email", status_code=status.HTTP_201_CREATED)
async def import_email(
    matter_id: uuid.UUID,
    payload: ImportEmailIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Called by the Outlook taskpane (frontend /outlook): the email body
    becomes a matter note, attachments go through the standard document
    pipeline (encrypt -> OCR -> index -> deadline scan)."""
    import base64

    from app.models import MatterNote

    await get_owned_matter(db, user, matter_id)
    if not payload.body.strip() and not payload.attachments:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty email")

    header = "\n".join(
        line for line in (
            f"📧 {payload.subject.strip()}" if payload.subject.strip() else "📧 Email",
            f"Nga / Von: {payload.sender.strip()}" if payload.sender.strip() else "",
            f"Data: {payload.received_at.strip()}" if payload.received_at.strip() else "",
        ) if line
    )
    note = MatterNote(
        tenant_id=user.tenant_id,
        matter_id=matter_id,
        author_id=user.id,
        body=f"{header}\n\n{payload.body.strip()[:50000]}".strip(),
    )
    db.add(note)

    saved_docs: list[str] = []
    skipped: list[str] = []
    for att in payload.attachments[:20]:
        try:
            content = base64.b64decode(att.content_base64, validate=True)
        except Exception:
            skipped.append(att.name)
            continue
        if not content or len(content) > MAX_UPLOAD_BYTES:
            skipped.append(att.name)
            continue
        if not upload_type_allowed(att.name, None):
            skipped.append(att.name)
            continue
        rel_path, sha, encrypted = storage.save_file(content, user.tenant_id)
        text, ocr_status = storage.extract_text(
            content, "application/octet-stream", att.name
        )
        doc = Document(
            tenant_id=user.tenant_id,
            matter_id=matter_id,
            family_id=uuid.uuid4(),
            version=1,
            is_latest=True,
            filename=att.name[:255],
            mime_type="application/octet-stream",
            size_bytes=len(content),
            sha256=sha,
            storage_path=rel_path,
            encrypted=encrypted,
            category="correspondence",
            uploaded_by_id=user.id,
            text_content=text or None,
            ocr_status=ocr_status,
        )
        db.add(doc)
        await db.flush()
        if text:
            await rag.index_document_chunks(db, doc)
        saved_docs.append(str(doc.id))

    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="matter.import_email",
        entity_type="matter", entity_id=str(matter_id),
        details={
            "subject": payload.subject[:200],
            "attachments": len(saved_docs),
            "skipped": skipped[:10],
        },
    )
    await db.commit()
    for doc_id in saved_docs:
        deadline_suggest.scan_document_background(uuid.UUID(doc_id))
    return {"note": True, "documents": len(saved_docs), "skipped": skipped}


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


@router.get("/documents/{document_id}/preview")
async def preview_document(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Serve the file inline so the browser can render it (PDF viewer, images)."""
    doc = await _get_owned_document(db, user, document_id)
    content = storage.load_file(doc.storage_path, doc.encrypted)
    return Response(
        content=content,
        media_type=doc.mime_type,
        headers={"Content-Disposition": f'inline; filename="{doc.filename}"'},
    )


class VisibilityIn(BaseModel):
    visible: bool


def require_ai_review(doc: Document) -> None:
    """BRAK KI-Leitfaden human oversight (D-044): an AI-generated document
    may not leave the firm before a human confirms they reviewed it."""
    if doc.ai_generated and doc.ai_reviewed_at is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "AI-generated document requires human review confirmation first",
        )


@router.post("/documents/{document_id}/confirm-ai-review", response_model=DocumentOut)
async def confirm_ai_review(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """The lawyer confirms they reviewed the AI-generated document — the
    review point required before sharing/signature (BRAK KI-Leitfaden)."""
    doc = await _get_owned_document(db, user, document_id)
    if not doc.ai_generated:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Document is not AI-generated")
    doc.ai_reviewed_by_id = user.id
    doc.ai_reviewed_at = datetime.now(UTC)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="document.ai_review_confirm",
        entity_type="document", entity_id=str(doc.id), details={"filename": doc.filename},
    )
    await db.commit()
    await db.refresh(doc)
    return _to_out(doc)


@router.post("/documents/{document_id}/visibility", response_model=DocumentOut)
async def set_document_visibility(
    document_id: uuid.UUID,
    body: VisibilityIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Share/unshare a document with the client in the portal."""
    doc = await _get_owned_document(db, user, document_id)
    if body.visible:
        require_ai_review(doc)
    doc.visible_to_client = body.visible
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="document.visibility",
        entity_type="document", entity_id=str(doc.id), details={"visible": body.visible},
    )
    await db.commit()
    await db.refresh(doc)
    return _to_out(doc)


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
    doc = await _get_owned_document(db, user, document_id)
    return {"text": doc.text_content or "", "ocr_status": doc.ocr_status}


@router.post("/documents/{document_id}/summarize")
async def summarize_document(
    document_id: uuid.UUID,
    force: bool = False,
    provider: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI summary of the extracted text (summary + key points + possible
    deadlines). Cached in documents.ai_summary; force=true recomputes."""
    import json as jsonlib

    from app.api.assistant import _effective_provider
    from app.services.assistant import summarize_document_text

    doc = await _get_owned_document(db, user, document_id)
    if doc.ai_summary and not force:
        return jsonlib.loads(doc.ai_summary)
    if not doc.text_content or len(doc.text_content.strip()) < 40:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Document has no extracted text"
        )
    provider_name = await _effective_provider(db, user, provider)
    try:
        result = await summarize_document_text(doc.text_content, provider_name)
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
    if result is None:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "AI reply could not be parsed; try again"
        )
    doc.ai_summary = jsonlib.dumps(result, ensure_ascii=False)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="document.summarize",
        entity_type="document", entity_id=str(doc.id),
    )
    await db.commit()
    return result
