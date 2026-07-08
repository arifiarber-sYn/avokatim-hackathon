"""Firm profile: name and fiscal identity printed on invoices (Kosovo NUI/VAT)."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models import Tenant, User
from app.services.audit import log_action

router = APIRouter(prefix="/firm", tags=["firm"])


class FirmOut(BaseModel):
    name: str
    kind: str
    fiscal_number: str | None
    vat_number: str | None
    address: str | None
    default_vat_rate: int

    model_config = {"from_attributes": True}


class FirmUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    fiscal_number: str | None = None
    vat_number: str | None = None
    address: str | None = None
    default_vat_rate: int | None = Field(None, ge=0, le=30)


@router.get("", response_model=FirmOut)
async def get_firm(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tenant = await db.get(Tenant, user.tenant_id)
    return tenant


@router.patch("", response_model=FirmOut)
async def update_firm(
    body: FirmUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin only")
    tenant = await db.get(Tenant, user.tenant_id)
    changes = body.model_dump(exclude_unset=True)
    for k, v in changes.items():
        setattr(tenant, k, v)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="firm.update",
        entity_type="tenant", entity_id=str(tenant.id), details={"fields": list(changes)},
    )
    await db.commit()
    await db.refresh(tenant)
    return tenant
