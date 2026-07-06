import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.matters import get_owned_matter
from app.database import get_db
from app.deps import get_current_user
from app.models import Document, User
from app.schemas.documents import DocumentOut
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
