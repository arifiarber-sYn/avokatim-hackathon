"""Lawyer-side collaboration endpoints: matter messages, e-signature requests,
AI deadline extraction from court documents, AI client-update drafting."""
import logging
import uuid
from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.matters import get_owned_matter
from app.database import get_db
from app.deps import get_current_user
from app.models import (
    Contact,
    Deadline,
    Document,
    MatterMessage,
    SignatureRequest,
    User,
)
from app.services.assistant import draft_client_update, extract_deadlines_from_text
from app.services.audit import log_action

logger = logging.getLogger(__name__)
router = APIRouter(tags=["collab"])


# ---------- Matter messages (lawyer side) ----------

class MessageIn(BaseModel):
    body: str


class MessageOut(BaseModel):
    id: uuid.UUID
    matter_id: uuid.UUID
    sender_user_id: uuid.UUID | None
    sender_contact_id: uuid.UUID | None
    body: str
    read_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/matters/{matter_id}/messages", response_model=list[MessageOut])
async def list_messages(
    matter_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_owned_matter(db, user, matter_id)
    rows = (
        await db.execute(
            select(MatterMessage)
            .where(MatterMessage.matter_id == matter_id)
            .order_by(MatterMessage.created_at)
            .limit(500)
        )
    ).scalars().all()
    now = datetime.now(UTC)
    for m in rows:
        if m.sender_contact_id is not None and m.read_at is None:
            m.read_at = now
    await db.commit()
    return rows


@router.post("/matters/{matter_id}/messages", response_model=MessageOut, status_code=201)
async def send_message(
    matter_id: uuid.UUID,
    body: MessageIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_owned_matter(db, user, matter_id)
    if not body.body.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty message")
    message = MatterMessage(
        tenant_id=user.tenant_id,
        matter_id=matter_id,
        sender_user_id=user.id,
        body=body.body.strip(),
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


# ---------- E-signature requests (lawyer side) ----------

class SignatureRequestIn(BaseModel):
    document_id: uuid.UUID
    contact_id: uuid.UUID
    note: str | None = None


class SignatureRequestOut(BaseModel):
    id: uuid.UUID
    matter_id: uuid.UUID
    document_id: uuid.UUID
    contact_id: uuid.UUID
    status: str
    document_sha256: str
    signer_name: str | None
    signed_at: datetime | None
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/matters/{matter_id}/signatures", response_model=list[SignatureRequestOut])
async def list_signature_requests(
    matter_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_owned_matter(db, user, matter_id)
    return (
        await db.execute(
            select(SignatureRequest)
            .where(SignatureRequest.matter_id == matter_id)
            .order_by(SignatureRequest.created_at.desc())
        )
    ).scalars().all()


@router.post(
    "/matters/{matter_id}/signatures", response_model=SignatureRequestOut, status_code=201
)
async def request_signature(
    matter_id: uuid.UUID,
    body: SignatureRequestIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_owned_matter(db, user, matter_id)
    document = await db.get(Document, body.document_id)
    if document is None or document.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    contact = await db.get(Contact, body.contact_id)
    if contact is None or contact.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contact not found")
    if not contact.portal_enabled:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Contact has no portal access — invite them first"
        )

    request = SignatureRequest(
        tenant_id=user.tenant_id,
        matter_id=matter_id,
        document_id=body.document_id,
        contact_id=body.contact_id,
        requested_by_id=user.id,
        document_sha256=document.sha256,
        note=body.note,
    )
    db.add(request)
    await db.flush()
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="signature.request",
        entity_type="signature_request", entity_id=str(request.id),
        details={"document": document.filename},
    )
    await db.commit()
    await db.refresh(request)
    return request


# ---------- AI: deadline extraction from a court document ----------

class ExtractedDeadline(BaseModel):
    title: str
    kind: str = "deadline"
    due_date: date | None = None
    trigger_date: date | None = None
    days: int | None = None
    legal_basis: str | None = None
    confidence: str = "medium"


@router.post(
    "/matters/{matter_id}/documents/{document_id}/extract-deadlines",
    response_model=list[ExtractedDeadline],
)
async def extract_deadlines(
    matter_id: uuid.UUID,
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bora reads a court document and proposes deadlines. The lawyer reviews
    each proposal before anything is saved."""
    await get_owned_matter(db, user, matter_id)
    document = await db.get(Document, document_id)
    if document is None or document.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    if not document.text_content:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Document has no extracted text (OCR pending?)"
        )
    try:
        raw = await extract_deadlines_from_text(document.text_content)
    except Exception as exc:
        logger.warning("Deadline extraction failed: %s", exc)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "AI provider unavailable")

    proposals: list[ExtractedDeadline] = []
    for item in raw[:10]:
        if not isinstance(item, dict):
            continue
        item["due_date"] = item.pop("date", None)
        try:
            proposals.append(ExtractedDeadline(**{
                k: item.get(k) for k in
                ("title", "kind", "due_date", "trigger_date", "days", "legal_basis", "confidence")
                if item.get(k) is not None
            }))
        except Exception:
            continue
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="ai.extract_deadlines",
        entity_type="document", entity_id=str(document.id),
        details={"proposals": len(proposals)},
    )
    await db.commit()
    return proposals


class AcceptDeadlinesIn(BaseModel):
    deadlines: list[ExtractedDeadline]


@router.post("/matters/{matter_id}/deadlines/bulk", status_code=201)
async def accept_extracted_deadlines(
    matter_id: uuid.UUID,
    body: AcceptDeadlinesIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Persist the proposals the lawyer accepted."""
    await get_owned_matter(db, user, matter_id)
    created = 0
    for item in body.deadlines:
        if item.due_date is None:
            continue
        d = item.due_date
        deadline = Deadline(
            tenant_id=user.tenant_id,
            matter_id=matter_id,
            kind=item.kind if item.kind in ("deadline", "hearing", "meeting") else "deadline",
            title=item.title,
            due_at=datetime(d.year, d.month, d.day, 16, 0, tzinfo=UTC),
            trigger_date=item.trigger_date,
            legal_basis=item.legal_basis,
        )
        db.add(deadline)
        created += 1
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="deadline.bulk_create_ai",
        entity_type="matter", entity_id=str(matter_id), details={"created": created},
    )
    await db.commit()
    return {"created": created}


# ---------- AI: client update draft ----------

class ClientUpdateIn(BaseModel):
    instructions: str | None = None


@router.post("/matters/{matter_id}/client-update-draft")
async def client_update_draft(
    matter_id: uuid.UUID,
    body: ClientUpdateIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_owned_matter(db, user, matter_id)
    try:
        draft = await draft_client_update(
            db, matter_id=matter_id, extra_instructions=body.instructions
        )
    except Exception as exc:
        logger.warning("Client update draft failed: %s", exc)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "AI provider unavailable")
    return {"draft": draft}
