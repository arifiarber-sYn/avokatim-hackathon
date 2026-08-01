"""Firm profile: name and fiscal identity printed on invoices (Kosovo NUI/VAT)."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.jurisdictions import is_valid_region
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
    # Structured IBAN for e-invoices (ZUGFeRD SEPA payment means, DE)
    iban: str | None = None
    default_vat_rate: int
    # DATEV export config (DE): Steuerberater + SKR03 accounts
    datev_consultant_no: str | None = None
    datev_client_no: str | None = None
    datev_revenue_account: str | None = None
    datev_debtor_account: str | None = None
    # Sub-national unit (DE: Bundesland code) — regional holiday calendar
    region: str | None = None
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
    iban: str | None = Field(None, max_length=34)
    datev_consultant_no: str | None = Field(None, max_length=7)
    datev_client_no: str | None = Field(None, max_length=5)
    datev_revenue_account: str | None = Field(None, max_length=9)
    datev_debtor_account: str | None = Field(None, max_length=9)
    default_vat_rate: int | None = Field(None, ge=0, le=30)
    region: str | None = Field(None, max_length=8)
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
    if "region" in changes and changes["region"]:
        changes["region"] = changes["region"].upper()
        if not is_valid_region(tenant.country, changes["region"]):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown region code")
    for k, v in changes.items():
        setattr(tenant, k, v)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="firm.update",
        entity_type="tenant", entity_id=str(tenant.id), details={"fields": list(changes)},
    )
    await db.commit()
    await db.refresh(tenant)
    return tenant
