"""Firm profile: name and fiscal identity printed on invoices (Kosovo NUI/VAT)."""
import uuid

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
    bank_details: str | None = None
    default_vat_rate: int
    logo: str | None = None
    require_2fa: bool = False
    # Data protection (Law 06/L-082)
    retention_years: int = 10
    allow_external_ai: bool = True
    # AML (Law 05/L-096)
    compliance_officer_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}


class FirmUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    fiscal_number: str | None = None
    vat_number: str | None = None
    address: str | None = None
    # Bank name + IBAN printed in the payment instructions on invoices
    bank_details: str | None = Field(None, max_length=500)
    default_vat_rate: int | None = Field(None, ge=0, le=30)
    # Small logo as a data URL (~max 200 KB) shown on portal + public intake
    logo: str | None = Field(None, max_length=280_000)
    require_2fa: bool | None = None
    retention_years: int | None = Field(None, ge=1, le=100)
    allow_external_ai: bool | None = None
    compliance_officer_id: uuid.UUID | None = None


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
