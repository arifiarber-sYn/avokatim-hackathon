"""Firm profile: name and fiscal identity printed on invoices (Kosovo NUI/VAT)."""
import csv
import io
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.jurisdictions import is_valid_region, profile_for
from app.models import AuditLog, Tenant, User
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


# ---------- KI-Nutzung register (D-044, BRAK KI-Leitfaden) ----------
# The office's own record of AI use, built from the append-only audit trail:
# which AI actions ran, how often, by whom, through which provider and where
# the data was processed. Document indexing/embeddings are always local.

_AI_ACTION_FILTER = or_(
    AuditLog.action.like("assistant.%"),
    AuditLog.action.like("ai.%"),
    AuditLog.action == "template.ai_assist",
    AuditLog.action == "deadline.bulk_create_ai",
)


def _ai_provider_info(tenant: Tenant) -> dict:
    name = profile_for(tenant.country).llm_provider or settings.llm_provider
    return {
        "name": name,
        # LocalProvider (Ollama) runs on this machine; anything else is an
        # external API. Embeddings/indexing are local by hard rule §5.7.
        "external": name != "local",
        "embeddings": "local",
        "allow_external_ai": tenant.allow_external_ai,
    }


def _require_admin(user: User) -> None:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin only")


@router.get("/ai-usage")
async def ai_usage_register(
    days: int = 90,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Per-office AI usage summary for the given window (default 90 days)."""
    _require_admin(user)
    days = max(1, min(days, 730))
    tenant = await db.get(Tenant, user.tenant_id)
    since = datetime.now(UTC) - timedelta(days=days)
    base = (
        select(AuditLog)
        .where(
            AuditLog.tenant_id == user.tenant_id,
            AuditLog.at >= since,
            _AI_ACTION_FILTER,
        )
    ).subquery()

    by_action = (
        await db.execute(
            select(base.c.action, func.count(), func.max(base.c.at))
            .group_by(base.c.action)
            .order_by(func.count().desc())
        )
    ).all()
    by_user = (
        await db.execute(
            select(User.full_name, func.count())
            .join_from(base, User, User.id == base.c.user_id)
            .group_by(User.full_name)
            .order_by(func.count().desc())
        )
    ).all()
    total = sum(count for _, count, _ in by_action)
    return {
        "since": since.isoformat(),
        "days": days,
        "total": total,
        "provider": _ai_provider_info(tenant),
        "actions": [
            {"action": action, "count": count, "last_at": last.isoformat()}
            for action, count, last in by_action
        ],
        "users": [{"name": name, "count": count} for name, count in by_user],
    }


@router.get("/ai-usage.csv")
async def ai_usage_csv(
    days: int = 90,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """The full register as CSV — one row per AI action (Art. 5 II DSGVO
    accountability; BRAK KI-Leitfaden documentation duty)."""
    _require_admin(user)
    days = max(1, min(days, 730))
    tenant = await db.get(Tenant, user.tenant_id)
    provider = _ai_provider_info(tenant)
    since = datetime.now(UTC) - timedelta(days=days)
    rows = (
        await db.execute(
            select(AuditLog, User.full_name)
            .outerjoin(User, User.id == AuditLog.user_id)
            .where(
                AuditLog.tenant_id == user.tenant_id,
                AuditLog.at >= since,
                _AI_ACTION_FILTER,
            )
            .order_by(AuditLog.at.desc())
            .limit(20000)
        )
    ).all()
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(
        ["timestamp", "user", "action", "entity_type", "entity_id",
         "provider", "provider_location", "embeddings"]
    )
    location = "local" if not provider["external"] else "external-api"
    for entry, full_name in rows:
        writer.writerow([
            entry.at.isoformat(), full_name or "", entry.action,
            entry.entity_type or "", entry.entity_id or "",
            provider["name"], location, "local",
        ])
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="firm.ai_usage_export",
        entity_type="tenant", entity_id=str(user.tenant_id),
        details={"days": days, "rows": len(rows)},
    )
    await db.commit()
    return Response(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="ki-nutzung-{days}d.csv"'
        },
    )


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
