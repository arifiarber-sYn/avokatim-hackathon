"""Client portal: a client logs in with email + portal password and sees the
status, deadlines (hearings only), messages and signature requests of their matters."""
import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import Contact, Deadline, Matter, MatterMessage, SignatureRequest, Tenant, User
from app.security import hash_password, verify_password
from app.services.audit import log_action
from app.i18n import pick_locale, tr
from app.services.notifications import send_email

router = APIRouter(prefix="/portal", tags=["portal"])
portal_bearer = HTTPBearer(auto_error=False)


class PortalInviteIn(BaseModel):
    contact_id: uuid.UUID
    password: str


class PortalLoginIn(BaseModel):
    email: EmailStr
    password: str


@router.post("/invite")
async def invite_client(
    body: PortalInviteIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """The lawyer enables portal access for a client contact."""
    contact = await db.get(Contact, body.contact_id)
    if contact is None or contact.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contact not found")
    if not contact.email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Contact has no email")
    contact.portal_password_hash = hash_password(body.password)
    contact.portal_enabled = True
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="portal.invite",
        entity_type="contact", entity_id=str(contact.id),
    )
    await db.commit()
    return {"enabled": True}


@router.post("/login")
async def portal_login(body: PortalLoginIn, db: AsyncSession = Depends(get_db)):
    # The same email can be a client of several firms (tenants); the password
    # decides which portal account this login belongs to.
    candidates = (
        await db.execute(
            select(Contact).where(
                Contact.email == body.email.lower(), Contact.portal_enabled.is_(True)
            )
        )
    ).scalars().all()
    contact = next(
        (
            c for c in candidates
            if c.portal_password_hash and verify_password(body.password, c.portal_password_hash)
        ),
        None,
    )
    if contact is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    now = datetime.now(UTC)
    token = pyjwt.encode(
        {"portal_contact": str(contact.id), "iat": now, "exp": now + timedelta(hours=12)},
        settings.secret_key,
        algorithm="HS256",
    )
    tenant = await db.get(Tenant, contact.tenant_id)
    return {
        "access_token": token,
        "client_name": contact.display_name,
        "firm_name": tenant.name if tenant else "BoraLaw",
        "firm_logo": tenant.logo if tenant else None,
    }


async def _portal_contact(
    creds: HTTPAuthorizationCredentials | None = Depends(portal_bearer),
    db: AsyncSession = Depends(get_db),
) -> Contact:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = pyjwt.decode(creds.credentials, settings.secret_key, algorithms=["HS256"])
        contact_id = uuid.UUID(payload["portal_contact"])
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    contact = await db.get(Contact, contact_id)
    if contact is None or not contact.portal_enabled:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Portal access disabled")
    return contact


@router.get("/my-matters")
async def my_matters(
    contact: Contact = Depends(_portal_contact),
    db: AsyncSession = Depends(get_db),
):
    matters = (
        await db.execute(
            select(Matter).where(
                Matter.client_id == contact.id, Matter.status.notin_(["archived"])
            )
        )
    ).scalars().all()
    result = []
    for m in matters:
        hearings = (
            await db.execute(
                select(Deadline).where(
                    Deadline.matter_id == m.id,
                    Deadline.kind == "hearing",
                    Deadline.status == "pending",
                )
            )
        ).scalars().all()
        result.append(
            {
                "id": str(m.id),
                "reference": m.reference,
                "title": m.title,
                "status": m.status,
                "court_name": m.court_name,
                "upcoming_hearings": [
                    {"title": h.title, "at": h.due_at.isoformat()} for h in hearings
                ],
            }
        )
    return result


async def _owned_portal_matter(
    db: AsyncSession, contact: Contact, matter_id: uuid.UUID
) -> Matter:
    matter = await db.get(Matter, matter_id)
    if matter is None or matter.client_id != contact.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Matter not found")
    return matter


# ---------- Messages (client side) ----------

class PortalMessageIn(BaseModel):
    body: str


@router.get("/matters/{matter_id}/messages")
async def portal_messages(
    matter_id: uuid.UUID,
    contact: Contact = Depends(_portal_contact),
    db: AsyncSession = Depends(get_db),
):
    await _owned_portal_matter(db, contact, matter_id)
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
        if m.sender_user_id is not None and m.read_at is None:
            m.read_at = now
    await db.commit()
    return [
        {
            "id": str(m.id),
            "from_client": m.sender_contact_id is not None,
            "body": m.body,
            "created_at": m.created_at.isoformat(),
        }
        for m in rows
    ]


@router.post("/matters/{matter_id}/messages", status_code=201)
async def portal_send_message(
    matter_id: uuid.UUID,
    body: PortalMessageIn,
    contact: Contact = Depends(_portal_contact),
    db: AsyncSession = Depends(get_db),
):
    matter = await _owned_portal_matter(db, contact, matter_id)
    if not body.body.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty message")
    message = MatterMessage(
        tenant_id=matter.tenant_id,
        matter_id=matter_id,
        sender_contact_id=contact.id,
        body=body.body.strip()[:5000],
    )
    db.add(message)
    await db.commit()
    lawyer = await db.get(User, matter.responsible_user_id)
    if lawyer and lawyer.email:
        loc = pick_locale(lawyer.locale)
        await send_email(
            lawyer.email,
            tr(loc, "email_new_message_subject", ref=matter.reference),
            (
                tr(loc, "email_new_message_body",
                   client=contact.display_name, title=matter.title)
                + f"\n\n{message.body[:500]}\n\n"
                f"{settings.public_base_url}/matters/{matter.id}\n"
            ),
        )
    return {"id": str(message.id)}


# ---------- Documents (client side) ----------

@router.get("/matters/{matter_id}/documents")
async def portal_documents(
    matter_id: uuid.UUID,
    contact: Contact = Depends(_portal_contact),
    db: AsyncSession = Depends(get_db),
):
    """Documents the lawyer marked as visible to the client."""
    from app.models import Document

    await _owned_portal_matter(db, contact, matter_id)
    rows = (
        await db.execute(
            select(Document)
            .where(
                Document.matter_id == matter_id,
                Document.is_latest.is_(True),
                Document.visible_to_client.is_(True),
            )
            .order_by(Document.created_at.desc())
        )
    ).scalars().all()
    return [
        {
            "id": str(d.id),
            "filename": d.filename,
            "mime_type": d.mime_type,
            "size_bytes": d.size_bytes,
            "category": d.category,
            "created_at": d.created_at.isoformat(),
        }
        for d in rows
    ]


@router.get("/documents/{document_id}/download")
async def portal_download_document(
    document_id: uuid.UUID,
    contact: Contact = Depends(_portal_contact),
    db: AsyncSession = Depends(get_db),
):
    from fastapi.responses import Response

    from app.models import Document
    from app.services import storage

    doc = await db.get(Document, document_id)
    if doc is None or not doc.visible_to_client or doc.matter_id is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    await _owned_portal_matter(db, contact, doc.matter_id)
    content = storage.load_file(doc.storage_path, doc.encrypted)
    await log_action(
        db, tenant_id=doc.tenant_id, user_id=None, action="portal.document_download",
        entity_type="document", entity_id=str(doc.id),
        details={"contact": contact.display_name},
    )
    await db.commit()
    return Response(
        content=content,
        media_type=doc.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{doc.filename}"'},
    )


# ---------- Signature requests (client side) ----------

class PortalSignIn(BaseModel):
    signer_name: str


@router.get("/signatures")
async def portal_signatures(
    contact: Contact = Depends(_portal_contact),
    db: AsyncSession = Depends(get_db),
):
    rows = (
        await db.execute(
            select(SignatureRequest)
            .where(SignatureRequest.contact_id == contact.id)
            .order_by(SignatureRequest.created_at.desc())
        )
    ).scalars().all()
    result = []
    for r in rows:
        from app.models import Document

        document = await db.get(Document, r.document_id)
        result.append(
            {
                "id": str(r.id),
                "document_name": document.filename if document else "?",
                "status": r.status,
                "note": r.note,
                "requested_at": r.created_at.isoformat(),
                "signed_at": r.signed_at.isoformat() if r.signed_at else None,
                "document_sha256": r.document_sha256,
            }
        )
    return result


@router.post("/signatures/{request_id}/sign")
async def portal_sign(
    request_id: uuid.UUID,
    body: PortalSignIn,
    request: Request,
    contact: Contact = Depends(_portal_contact),
    db: AsyncSession = Depends(get_db),
):
    sig = await db.get(SignatureRequest, request_id)
    if sig is None or sig.contact_id != contact.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Signature request not found")
    if sig.status != "pending":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Already resolved")
    if not body.signer_name.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Signer name required")

    sig.status = "signed"
    sig.signer_name = body.signer_name.strip()
    sig.signer_ip = request.client.host if request.client else None
    sig.signed_at = datetime.now(UTC)
    await log_action(
        db, tenant_id=sig.tenant_id, user_id=None, action="signature.signed",
        entity_type="signature_request", entity_id=str(sig.id),
        details={"signer": sig.signer_name, "ip": sig.signer_ip,
                 "sha256": sig.document_sha256},
    )
    await db.commit()
    requester = await db.get(User, sig.requested_by_id) if sig.requested_by_id else None
    if requester and requester.email:
        loc = pick_locale(requester.locale)
        await send_email(
            requester.email,
            tr(loc, "email_signed_subject"),
            (
                tr(loc, "email_signed_body",
                   client=contact.display_name, request_id=sig.id)
                + f"\n\n{settings.public_base_url}/matters/{sig.matter_id}\n"
            ),
        )
    return {"status": "signed", "signed_at": sig.signed_at.isoformat()}


@router.post("/signatures/{request_id}/decline")
async def portal_decline_signature(
    request_id: uuid.UUID,
    contact: Contact = Depends(_portal_contact),
    db: AsyncSession = Depends(get_db),
):
    sig = await db.get(SignatureRequest, request_id)
    if sig is None or sig.contact_id != contact.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Signature request not found")
    if sig.status != "pending":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Already resolved")
    sig.status = "declined"
    await log_action(
        db, tenant_id=sig.tenant_id, user_id=None, action="signature.declined",
        entity_type="signature_request", entity_id=str(sig.id),
    )
    await db.commit()
    return {"status": "declined"}
