import logging
import secrets
import uuid
from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.matters import _next_reference
from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.i18n import pick_locale, tr
from app.jurisdictions import jurisdiction_row_for_tenant
from app.models import (
    CaseRequest,
    CitizenUser,
    Contact,
    IntakeRequest,
    Matter,
    MatterParty,
    Tenant,
    User,
)
from app.schemas.matters import IntakeIn, IntakeOut
from app.services.audit import log_action
from app.services.conflicts import check_conflicts
from app.services.consent import grant_consent
from app.services.assistant import classify_intake
from app.services.notifications import send_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/intake", tags=["intake"])
public_router = APIRouter(prefix="/public", tags=["public"])


@router.get("", response_model=list[IntakeOut])
async def list_intakes(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(IntakeRequest)
        .where(IntakeRequest.tenant_id == user.tenant_id)
        .order_by(IntakeRequest.created_at.desc())
        .limit(200)
    )
    return (await db.execute(stmt)).scalars().all()


@router.post("", response_model=IntakeOut, status_code=status.HTTP_201_CREATED)
async def create_intake(
    body: IntakeIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Capture a prospective case, run the conflict check immediately, and
    attempt AI classification (non-blocking if the LLM is unavailable)."""
    conflict = await check_conflicts(
        db, user.tenant_id, [body.client_name, *body.opposing_names]
    )

    classification = None
    try:
        classification = await classify_intake(body.summary)
    except Exception as exc:  # LLM down / not configured — intake still works
        logger.warning("Intake AI classification skipped: %s", exc)

    intake = IntakeRequest(
        tenant_id=user.tenant_id,
        client_name=body.client_name,
        client_email=body.client_email,
        client_phone=body.client_phone,
        opposing_names=body.opposing_names,
        summary=body.summary,
        source=body.source,
        status="conflict" if conflict["has_conflicts"] else "new",
        conflict_result=conflict,
        ai_classification=classification,
    )
    db.add(intake)
    await db.flush()
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="intake.create",
        entity_type="intake", entity_id=str(intake.id),
        details={"has_conflicts": conflict["has_conflicts"]},
    )
    await db.commit()
    await db.refresh(intake)
    return intake


@router.post("/{intake_id}/accept", response_model=IntakeOut)
async def accept_intake(
    intake_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Convert an intake into a matter: creates the client contact, the matter,
    and opposing-party records in one step."""
    intake = await db.get(IntakeRequest, intake_id)
    if intake is None or intake.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Intake not found")
    if intake.status == "accepted":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Already accepted")

    client = Contact(
        tenant_id=user.tenant_id,
        display_name=intake.client_name,
        email=intake.client_email,
        phone=intake.client_phone,
    )
    db.add(client)
    await db.flush()

    practice_area = (intake.ai_classification or {}).get("practice_area", "civil")
    jurisdiction = await jurisdiction_row_for_tenant(db, user.tenant_id)
    matter = Matter(
        tenant_id=user.tenant_id,
        reference=await _next_reference(db, user.tenant_id, practice_area),
        title=(intake.ai_classification or {}).get("suggested_title")
        or f"Lënda e {intake.client_name}",
        description=intake.summary,
        practice_area=practice_area,
        jurisdiction_id=jurisdiction.id,
        responsible_user_id=user.id,
        client_id=client.id,
        opened_on=date.today(),
    )
    db.add(matter)
    await db.flush()

    for name in intake.opposing_names or []:
        opposing = Contact(tenant_id=user.tenant_id, display_name=name)
        db.add(opposing)
        await db.flush()
        db.add(MatterParty(matter_id=matter.id, contact_id=opposing.id, role="opposing_party"))

    intake.status = "accepted"
    intake.matter_id = matter.id

    # Marketplace conversion: the citizen becomes a portal client with the
    # same credentials as their citizen account.
    marketplace_citizen = None
    case = (
        await db.execute(
            select(CaseRequest).where(CaseRequest.intake_request_id == intake.id)
        )
    ).scalar_one_or_none()
    if case is not None:
        marketplace_citizen = await db.get(CitizenUser, case.citizen_id)
        if marketplace_citizen is not None:
            client.email = marketplace_citizen.email
            client.phone = marketplace_citizen.phone
            client.locale = marketplace_citizen.locale
            client.portal_password_hash = marketplace_citizen.password_hash
            client.portal_enabled = True
            # Carry the citizen's signup privacy consent into the tenant's
            # consent registry (Law 06/L-082 art. 7 — demonstrable consent)
            await grant_consent(
                db, tenant_id=user.tenant_id, contact_id=client.id,
                kind="portal_tos", method="marketplace",
                notes=(
                    "Accepted at citizen signup "
                    f"{marketplace_citizen.privacy_accepted_at.isoformat() if marketplace_citizen.privacy_accepted_at else '?'}"
                ),
            )
        case.status = "converted"
        case.contact_id = client.id

    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="intake.accept",
        entity_type="intake", entity_id=str(intake.id),
        details={"matter_reference": matter.reference,
                 "from_marketplace": case is not None},
    )
    await db.commit()
    await db.refresh(intake)

    if marketplace_citizen is not None:
        tenant = await db.get(Tenant, user.tenant_id)
        loc = pick_locale(marketplace_citizen.locale)
        await send_email(
            marketplace_citizen.email,
            tr(loc, "case_portal_ready_subject"),
            tr(loc, "case_portal_ready_body", firm=tenant.name,
               url=f"{settings.public_base_url}/portal"),
        )
    return intake


@router.get("/public-form")
async def get_public_form(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return (creating on first call) the tenant's public intake form URL."""
    tenant = await db.get(Tenant, user.tenant_id)
    if not tenant.intake_token:
        tenant.intake_token = secrets.token_urlsafe(24)
        await db.commit()
    return {"url": f"{settings.public_base_url}/apliko/{tenant.intake_token}"}


class PublicIntakeIn(BaseModel):
    client_name: str = Field(min_length=2, max_length=255)
    client_email: str | None = Field(default=None, max_length=255)
    client_phone: str | None = Field(default=None, max_length=64)
    summary: str = Field(min_length=10, max_length=8000)
    # Privacy-policy checkbox (Law 06/L-082) — must be true on the public form
    accept_privacy: bool = False


@public_router.get("/intake/{token}")
async def public_intake_info(token: str, db: AsyncSession = Depends(get_db)):
    """Practice name for the public form header. 404 keeps tokens unguessable."""
    tenant = (
        await db.execute(select(Tenant).where(Tenant.intake_token == token))
    ).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    return {"practice_name": tenant.name, "logo": tenant.logo}


@public_router.post("/intake/{token}", status_code=201)
async def public_intake_submit(
    token: str,
    body: PublicIntakeIn,
    db: AsyncSession = Depends(get_db),
):
    """Anonymous submission from the firm's public intake link. No AI here —
    classification happens when the lawyer opens the intake list."""
    tenant = (
        await db.execute(select(Tenant).where(Tenant.intake_token == token))
    ).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    if not body.accept_privacy:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Privacy policy must be accepted"
        )

    conflict = await check_conflicts(db, tenant.id, [body.client_name])
    intake = IntakeRequest(
        tenant_id=tenant.id,
        client_name=body.client_name,
        client_email=body.client_email,
        client_phone=body.client_phone,
        summary=body.summary,
        source="web",
        status="conflict" if conflict["has_conflicts"] else "new",
        conflict_result=conflict,
        tos_accepted_at=datetime.now(UTC),
    )
    db.add(intake)
    await db.flush()
    await log_action(
        db, tenant_id=tenant.id, user_id=None, action="intake.public_submit",
        entity_type="intake", entity_id=str(intake.id),
    )
    await db.commit()
    return {"received": True}


@router.post("/{intake_id}/decline", response_model=IntakeOut)
async def decline_intake(
    intake_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    intake = await db.get(IntakeRequest, intake_id)
    if intake is None or intake.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Intake not found")
    intake.status = "declined"
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="intake.decline",
        entity_type="intake", entity_id=str(intake.id),
    )
    await db.commit()
    await db.refresh(intake)
    return intake
