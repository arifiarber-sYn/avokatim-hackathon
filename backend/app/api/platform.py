"""Platform operator (superadmin) panel: cross-tenant administration."""
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import require_superadmin
from app.models import Matter, Tenant, User
from app.services.audit import log_action

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
    billing_notes: str | None
    created_at: str


class TenantUpdate(BaseModel):
    plan: str | None = Field(default=None, pattern="^(trial|solo|firm)$")
    seats_limit: int | None = Field(default=None, ge=1, le=500)
    extend_trial_days: int | None = Field(default=None, ge=1, le=365)
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
    if body.billing_notes is not None:
        tenant.billing_notes = body.billing_notes
    await log_action(
        db, tenant_id=tenant.id, user_id=admin.id, action="platform.update",
        details=body.model_dump(exclude_none=True),
    )
    await db.commit()
    return {"updated": True}
