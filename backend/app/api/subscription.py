"""Tenant-facing subscription billing: see the plan, upgrade from trial,
list platform invoices and pay by card when Stripe is configured.

The money flow is one-way: the tenant pays the platform operator a flat
per-seat subscription. Client fees always go directly to the lawyer."""
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.jurisdictions import profile_for
from app.models import PlatformInvoice, Tenant, User
from app.services.audit import log_action
from app.services.payments import create_payment_link, payments_enabled
from app.services.platform_billing import (
    active_seats,
    generate_invoice,
    has_past_due,
    invoice_out,
    tenant_is_billable,
)

router = APIRouter(prefix="/billing/subscription", tags=["subscription"])


def _require_admin(user: User) -> None:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin only")


@router.get("")
async def subscription_state(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    _require_admin(user)
    tenant = await db.get(Tenant, user.tenant_id)
    seats = await active_seats(db, tenant.id)
    price = Decimal(tenant.plan_price_eur or 0)
    invoices = (
        (
            await db.execute(
                select(PlatformInvoice)
                .where(PlatformInvoice.tenant_id == tenant.id)
                .order_by(PlatformInvoice.period_start.desc())
                .limit(24)
            )
        ).scalars().all()
    )
    return {
        "plan": tenant.plan,
        "status": tenant.status,
        "trial_ends_at": tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None,
        "price_eur": float(price),
        "seats": seats,
        "monthly_total_eur": float((price * seats).quantize(Decimal("0.01"))),
        "free_forever": tenant_is_billable(tenant) is False and tenant.plan != "trial" and price == 0,
        "past_due": await has_past_due(db, tenant.id),
        "card_payments": payments_enabled(),
        "bank_details": settings.platform_bank_details or None,
        "invoices": [invoice_out(i) for i in invoices],
    }


@router.post("/upgrade")
async def upgrade_to_paid(
    background: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Self-service move from trial to the paid plan (solo or firm, matching
    the practice kind). The first monthly invoice is issued immediately."""
    _require_admin(user)
    tenant = await db.get(Tenant, user.tenant_id)
    if tenant.plan != "trial":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Already on a paid plan")
    tenant.plan = "firm" if tenant.kind == "firm" else "solo"
    tenant.trial_ends_at = None
    invoice = await generate_invoice(db, tenant)
    await log_action(
        db, tenant_id=tenant.id, user_id=user.id, action="subscription.upgrade",
        details={"plan": tenant.plan, "price_eur": str(tenant.plan_price_eur)},
    )
    await db.commit()
    if invoice is not None:
        from app.services.platform_billing import email_invoice_by_id

        background.add_task(email_invoice_by_id, invoice.id)
    return {
        "plan": tenant.plan,
        "invoice": invoice_out(invoice) if invoice is not None else None,
    }


@router.post("/invoices/{invoice_id}/payment-link")
async def subscription_payment_link(
    invoice_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_admin(user)
    if not payments_enabled():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Card payments are not configured (Stripe)"
        )
    invoice = await db.get(PlatformInvoice, invoice_id)
    if invoice is None or invoice.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invoice not found")
    if invoice.status != "open":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invoice is already settled")
    tenant = await db.get(Tenant, user.tenant_id)
    brand = profile_for(tenant.country if tenant else None).brand_name
    try:
        url, session_id = await create_payment_link(
            invoice_id=str(invoice.id),
            invoice_number=invoice.number,
            amount_cents=int(invoice.amount_eur * 100),
            currency="EUR",
            description=f"{brand} {invoice.number} — {invoice.period_start:%m/%Y}",
            customer_email=user.email,
            metadata_key="platform_invoice_id",
            return_path="/settings",
        )
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc))
    invoice.payment_link = url
    invoice.stripe_session_id = session_id
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id,
        action="subscription.payment_link", entity_type="platform_invoice",
        entity_id=str(invoice.id), details={"session": session_id},
    )
    await db.commit()
    return invoice_out(invoice)
