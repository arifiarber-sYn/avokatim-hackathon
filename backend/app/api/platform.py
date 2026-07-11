"""Platform operator (superadmin) panel: cross-tenant administration."""
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import require_superadmin
from app.models import Matter, PlatformInvoice, Tenant, User
from app.services.audit import log_action
from app.services.platform_billing import generate_invoice, invoice_out

router = APIRouter(prefix="/platform", tags=["platform"])


class TenantRow(BaseModel):
    id: uuid.UUID
    name: str
    kind: str
    plan: str
    status: str
    seats_limit: int
    seats_used: int
    matters_count: int
    trial_ends_at: str | None
    plan_price_eur: float
    billing_notes: str | None
    created_at: str


class TenantUpdate(BaseModel):
    plan: str | None = Field(default=None, pattern="^(trial|solo|firm)$")
    seats_limit: int | None = Field(default=None, ge=1, le=500)
    extend_trial_days: int | None = Field(default=None, ge=1, le=365)
    plan_price_eur: float | None = Field(default=None, ge=0, le=1000)
    billing_notes: str | None = None


@router.get("/tenants", response_model=list[TenantRow])
async def list_tenants(
    admin: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    tenants = (
        (await db.execute(select(Tenant).order_by(Tenant.created_at))).scalars().all()
    )
    seat_counts = dict(
        (await db.execute(
            select(User.tenant_id, func.count(User.id))
            .where(User.is_active.is_(True))
            .group_by(User.tenant_id)
        )).all()
    )
    matter_counts = dict(
        (await db.execute(
            select(Matter.tenant_id, func.count(Matter.id)).group_by(Matter.tenant_id)
        )).all()
    )
    return [
        TenantRow(
            id=t.id,
            name=t.name,
            kind=t.kind,
            plan=t.plan,
            status=t.status,
            seats_limit=t.seats_limit,
            seats_used=seat_counts.get(t.id, 0),
            matters_count=matter_counts.get(t.id, 0),
            trial_ends_at=t.trial_ends_at.isoformat() if t.trial_ends_at else None,
            plan_price_eur=float(t.plan_price_eur or 0),
            billing_notes=t.billing_notes,
            created_at=t.created_at.isoformat(),
        )
        for t in tenants
    ]


async def _get_tenant(db: AsyncSession, tenant_id: uuid.UUID) -> Tenant:
    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant not found")
    return tenant


@router.post("/tenants/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: uuid.UUID,
    admin: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    tenant = await _get_tenant(db, tenant_id)
    if tenant.id == admin.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot suspend your own tenant")
    tenant.status = "suspended"
    tenant.suspended_at = datetime.now(UTC)
    await log_action(
        db, tenant_id=tenant.id, user_id=admin.id, action="platform.suspend"
    )
    await db.commit()
    return {"status": "suspended"}


@router.post("/tenants/{tenant_id}/activate")
async def activate_tenant(
    tenant_id: uuid.UUID,
    admin: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    tenant = await _get_tenant(db, tenant_id)
    tenant.status = "active"
    tenant.suspended_at = None
    await log_action(
        db, tenant_id=tenant.id, user_id=admin.id, action="platform.activate"
    )
    await db.commit()
    return {"status": "active"}


@router.patch("/tenants/{tenant_id}")
async def update_tenant(
    tenant_id: uuid.UUID,
    body: TenantUpdate,
    admin: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    tenant = await _get_tenant(db, tenant_id)
    if body.plan is not None:
        tenant.plan = body.plan
        if body.plan != "trial":
            tenant.trial_ends_at = None
    if body.seats_limit is not None:
        tenant.seats_limit = body.seats_limit
    if body.extend_trial_days is not None:
        base = tenant.trial_ends_at or datetime.now(UTC)
        if base < datetime.now(UTC):
            base = datetime.now(UTC)
        tenant.trial_ends_at = base + timedelta(days=body.extend_trial_days)
        tenant.plan = "trial"
    if body.plan_price_eur is not None:
        tenant.plan_price_eur = Decimal(str(body.plan_price_eur))
    if body.billing_notes is not None:
        tenant.billing_notes = body.billing_notes
    await log_action(
        db, tenant_id=tenant.id, user_id=admin.id, action="platform.update",
        details=body.model_dump(exclude_none=True),
    )
    await db.commit()
    return {"updated": True}


# ---------- platform subscription invoices ----------

@router.get("/invoices")
async def list_platform_invoices(
    status_filter: str | None = None,
    admin: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(PlatformInvoice, Tenant.name).join(
        Tenant, Tenant.id == PlatformInvoice.tenant_id
    )
    if status_filter:
        stmt = stmt.where(PlatformInvoice.status == status_filter)
    rows = (
        await db.execute(
            stmt.order_by(PlatformInvoice.issued_on.desc()).limit(500)
        )
    ).all()
    today = date.today()
    return [
        {
            **invoice_out(invoice),
            "tenant_name": tenant_name,
            "tenant_id": str(invoice.tenant_id),
            "overdue_days": max(0, (today - invoice.due_on).days)
            if invoice.status == "open" else 0,
        }
        for invoice, tenant_name in rows
    ]


@router.post("/invoices/generate")
async def generate_platform_invoices(
    admin: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Generate the current-month invoice for every billable tenant that
    doesn't have one yet (the daily loop does the same automatically)."""
    tenants = (await db.execute(select(Tenant))).scalars().all()
    created = []
    for tenant in tenants:
        invoice = await generate_invoice(db, tenant)
        if invoice is not None:
            created.append(invoice.number)
    await log_action(
        db, tenant_id=admin.tenant_id, user_id=admin.id,
        action="platform.invoices_generate", details={"created": created},
    )
    await db.commit()
    return {"created": created}


async def _get_platform_invoice(db: AsyncSession, invoice_id: uuid.UUID) -> PlatformInvoice:
    invoice = await db.get(PlatformInvoice, invoice_id)
    if invoice is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invoice not found")
    return invoice


class MarkPaidIn(BaseModel):
    payment_reference: str | None = Field(default=None, max_length=128)


@router.post("/invoices/{invoice_id}/mark-paid")
async def mark_platform_invoice_paid(
    invoice_id: uuid.UUID,
    body: MarkPaidIn,
    admin: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    invoice = await _get_platform_invoice(db, invoice_id)
    if invoice.status == "paid":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Already paid")
    invoice.status = "paid"
    invoice.paid_on = date.today()
    if body.payment_reference:
        invoice.payment_reference = body.payment_reference
    await log_action(
        db, tenant_id=invoice.tenant_id, user_id=admin.id,
        action="platform.invoice_paid", entity_type="platform_invoice",
        entity_id=str(invoice.id), details={"reference": body.payment_reference},
    )
    await db.commit()
    return invoice_out(invoice)


@router.post("/invoices/{invoice_id}/void")
async def void_platform_invoice(
    invoice_id: uuid.UUID,
    admin: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    invoice = await _get_platform_invoice(db, invoice_id)
    if invoice.status == "paid":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot void a paid invoice")
    invoice.status = "void"
    await log_action(
        db, tenant_id=invoice.tenant_id, user_id=admin.id,
        action="platform.invoice_void", entity_type="platform_invoice",
        entity_id=str(invoice.id),
    )
    await db.commit()
    return invoice_out(invoice)
