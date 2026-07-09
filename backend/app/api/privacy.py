"""Data-protection endpoints (Law No. 06/L-082): consent management per
contact, the right to erasure (anonymization), data-subject export, and the
retention review list."""
import io
import json
import uuid
import zipfile
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models import (
    ConsentRecord,
    Contact,
    Invoice,
    Matter,
    MatterMessage,
    Tenant,
    TrustTransaction,
    User,
)
from app.models.privacy import CONSENT_KINDS
from app.services.audit import log_action
from app.services.consent import grant_consent, revoke_consent

router = APIRouter(tags=["privacy"])


# ---------- Consents ----------

class ConsentOut(BaseModel):
    id: uuid.UUID
    kind: str
    granted_at: datetime
    revoked_at: datetime | None
    method: str
    ip: str | None

    model_config = {"from_attributes": True}


class ConsentIn(BaseModel):
    kind: str
    granted: bool
    notes: str | None = None


async def _owned_contact(db: AsyncSession, user: User, contact_id: uuid.UUID) -> Contact:
    contact = await db.get(Contact, contact_id)
    if contact is None or contact.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contact not found")
    return contact


@router.get("/contacts/{contact_id}/consents", response_model=list[ConsentOut])
async def list_consents(
    contact_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _owned_contact(db, user, contact_id)
    return (
        await db.execute(
            select(ConsentRecord)
            .where(ConsentRecord.contact_id == contact_id)
            .order_by(ConsentRecord.granted_at.desc())
        )
    ).scalars().all()


@router.post("/contacts/{contact_id}/consents", response_model=list[ConsentOut])
async def set_consent(
    contact_id: uuid.UUID,
    body: ConsentIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    contact = await _owned_contact(db, user, contact_id)
    if body.kind not in CONSENT_KINDS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown consent kind")
    if body.granted:
        await grant_consent(
            db,
            tenant_id=user.tenant_id,
            contact_id=contact.id,
            kind=body.kind,
            method="lawyer",
            ip=request.client.host if request.client else None,
            notes=body.notes,
        )
        action = "consent.grant"
    else:
        await revoke_consent(db, contact_id=contact.id, kind=body.kind)
        action = "consent.revoke"
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action=action,
        entity_type="contact", entity_id=str(contact.id), details={"kind": body.kind},
    )
    await db.commit()
    return (
        await db.execute(
            select(ConsentRecord)
            .where(ConsentRecord.contact_id == contact_id)
            .order_by(ConsentRecord.granted_at.desc())
        )
    ).scalars().all()


# ---------- Right to erasure (art. 17) ----------

@router.post("/contacts/{contact_id}/erasure")
async def erase_contact(
    contact_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Anonymize a contact's personal data. Matter files themselves are NOT
    deleted — professional and fiscal law obliges the lawyer to retain the
    case file; the personal identifiers are removed from the contact record.
    Blocked while the contact still has open matters."""
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin only")
    contact = await _owned_contact(db, user, contact_id)
    if contact.anonymized_at is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Already anonymized")

    open_matters = (
        await db.execute(
            select(Matter.id).where(
                Matter.client_id == contact.id,
                Matter.status.in_(["intake", "open", "on_hold"]),
            ).limit(1)
        )
    ).scalar_one_or_none()
    if open_matters is not None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Contact has open matters — close them before erasure",
        )

    short = str(contact.id)[:8]
    contact.display_name = f"Kontakt i anonimizuar {short}"
    contact.national_id = None
    contact.email = None
    contact.phone = None
    contact.address = None
    contact.notes = None
    contact.id_doc_type = None
    contact.id_doc_number = None
    contact.beneficial_owner = None
    contact.portal_enabled = False
    contact.portal_password_hash = None
    contact.anonymized_at = datetime.now(UTC)
    await revoke_consent(db, contact_id=contact.id, kind="portal_tos")
    for kind in CONSENT_KINDS:
        await revoke_consent(db, contact_id=contact.id, kind=kind)

    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="contact.erasure",
        entity_type="contact", entity_id=str(contact.id),
    )
    await db.commit()
    return {"anonymized": True, "display_name": contact.display_name}


# ---------- Data-subject export (art. 15/20) ----------

@router.get("/contacts/{contact_id}/export")
async def export_contact_data(
    contact_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """ZIP with everything the firm holds on one data subject — for
    answering access/portability requests."""
    contact = await _owned_contact(db, user, contact_id)

    matters = (
        await db.execute(select(Matter).where(Matter.client_id == contact.id))
    ).scalars().all()
    invoices = (
        await db.execute(
            select(Invoice)
            .where(Invoice.contact_id == contact.id)
            # total_with_vat is a Python property over items — eager-load them
            .options(selectinload(Invoice.items))
        )
    ).scalars().all()
    trust = (
        await db.execute(
            select(TrustTransaction).where(TrustTransaction.contact_id == contact.id)
        )
    ).scalars().all()
    messages = (
        await db.execute(
            select(MatterMessage).where(MatterMessage.sender_contact_id == contact.id)
        )
    ).scalars().all()
    consents = (
        await db.execute(
            select(ConsentRecord).where(ConsentRecord.contact_id == contact.id)
        )
    ).scalars().all()

    data = {
        "contact": {
            "display_name": contact.display_name,
            "kind": contact.kind,
            "national_id": contact.national_id,
            "email": contact.email,
            "phone": contact.phone,
            "address": contact.address,
            "locale": contact.locale,
            "created_at": contact.created_at.isoformat(),
        },
        "matters": [
            {
                "reference": m.reference,
                "title": m.title,
                "status": m.status,
                "opened_on": m.opened_on.isoformat() if m.opened_on else None,
                "closed_on": m.closed_on.isoformat() if m.closed_on else None,
            }
            for m in matters
        ],
        "invoices": [
            {
                "number": i.number,
                "status": i.status,
                "issued_on": i.issued_on.isoformat() if i.issued_on else None,
                "total_with_vat": str(i.total_with_vat),
                "currency": i.currency,
            }
            for i in invoices
        ],
        "trust_transactions": [
            {
                "kind": t.kind,
                "occurred_on": t.occurred_on.isoformat(),
                "amount": str(t.amount),
                "description": t.description,
            }
            for t in trust
        ],
        "messages": [
            {"created_at": m.created_at.isoformat(), "body": m.body} for m in messages
        ],
        "consents": [
            {
                "kind": c.kind,
                "granted_at": c.granted_at.isoformat(),
                "revoked_at": c.revoked_at.isoformat() if c.revoked_at else None,
                "method": c.method,
            }
            for c in consents
        ],
    }

    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "te-dhenat-e-subjektit.json",
            json.dumps(data, ensure_ascii=False, indent=2),
        )

    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="contact.data_export",
        entity_type="contact", entity_id=str(contact.id),
    )
    await db.commit()
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    return Response(
        content=zbuf.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition":
                f'attachment; filename="subjekti-{str(contact.id)[:8]}-{stamp}.zip"'
        },
    )


# ---------- Retention review (marking, never auto-delete) ----------

@router.get("/privacy/retention-review")
async def retention_review(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Matters closed longer ago than the firm's retention period. They are
    flagged for the lawyer's decision — legal practice forbids auto-deletion."""
    tenant = await db.get(Tenant, user.tenant_id)
    cutoff = date.today() - timedelta(days=365 * (tenant.retention_years or 10))
    rows = (
        await db.execute(
            select(Matter).where(
                Matter.tenant_id == user.tenant_id,
                Matter.status.in_(["closed", "archived"]),
                Matter.closed_on.is_not(None),
                Matter.closed_on <= cutoff,
            ).order_by(Matter.closed_on)
        )
    ).scalars().all()
    return {
        "retention_years": tenant.retention_years,
        "cutoff": cutoff.isoformat(),
        "matters": [
            {
                "id": str(m.id),
                "reference": m.reference,
                "title": m.title,
                "status": m.status,
                "closed_on": m.closed_on.isoformat(),
            }
            for m in rows
        ],
    }
