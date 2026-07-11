"""Public marketplace: citizens post case requests, lawyers claim them.

Two routers:
- public_router (/public/citizen, /public/lawyers): citizen auth + case CRUD,
  rate-limited by IP/account, email verification required to post.
- router (/marketplace): lawyer side — public profile, browse, claim, chat.

The claim runs the existing conflict check and creates an IntakeRequest with
source="marketplace"; the existing intake acceptance converts the citizen
into a Contact with portal access reusing the same password hash.
"""
import logging
import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import redis.asyncio as aioredis
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.i18n import pick_locale, tr
from app.models import (
    CaseRequest,
    CaseRequestMessage,
    CitizenUser,
    LawyerProfile,
    Tenant,
    User,
)
from app.models.matters import PRACTICE_AREAS
from app.security import (
    create_purpose_token,
    decode_purpose_token,
    hash_password,
    verify_password,
)
from app.services.audit import log_action
from app.services.conflicts import check_conflicts
from app.services.notifications import send_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/marketplace", tags=["marketplace"])
public_router = APIRouter(prefix="/public", tags=["public"])
citizen_bearer = HTTPBearer(auto_error=False)

CITIZEN_TOKEN_HOURS = 24 * 7


# ---------- abuse protection ----------

async def _rate_limit(action: str, key: str, limit: int, window_seconds: int) -> None:
    """Redis sliding counter; fails open if Redis is down (never lock everyone out)."""
    try:
        r = aioredis.from_url(settings.redis_url)
        rkey = f"avokatim:rl:{action}:{key}"
        pipe = r.pipeline()
        pipe.incr(rkey)
        pipe.expire(rkey, window_seconds)
        count, _ = await pipe.execute()
        await r.aclose()
        if int(count) > limit:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS, "Too many requests — try again later"
            )
    except HTTPException:
        raise
    except Exception:
        logger.warning("Rate limit unavailable for %s", action)


def _ip(request: Request) -> str:
    return request.client.host if request.client else "noip"


# ---------- citizen auth ----------

def _citizen_token(citizen_id: uuid.UUID) -> str:
    now = datetime.now(UTC)
    return pyjwt.encode(
        {"citizen": str(citizen_id), "iat": now,
         "exp": now + timedelta(hours=CITIZEN_TOKEN_HOURS)},
        settings.secret_key,
        algorithm="HS256",
    )


async def _current_citizen(
    creds: HTTPAuthorizationCredentials | None = Depends(citizen_bearer),
    db: AsyncSession = Depends(get_db),
) -> CitizenUser:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = pyjwt.decode(creds.credentials, settings.secret_key, algorithms=["HS256"])
        citizen_id = uuid.UUID(payload["citizen"])
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    citizen = await db.get(CitizenUser, citizen_id)
    if citizen is None or not citizen.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account disabled")
    return citizen


async def _send_citizen_verification(citizen_id: uuid.UUID, email: str, locale: str) -> None:
    token = create_purpose_token("citizen_verify", citizen_id, minutes=60 * 24 * 3)
    url = f"{settings.public_base_url}/rasti-im?verifiko={token}"
    loc = pick_locale(locale)
    await send_email(
        email, tr(loc, "citizen_verify_subject"), tr(loc, "citizen_verify_body", url=url)
    )


class CitizenSignupIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    locale: str = "sq"
    accept_privacy: bool = False


class CitizenLoginIn(BaseModel):
    email: EmailStr
    password: str


def _citizen_out(citizen: CitizenUser) -> dict:
    return {
        "id": str(citizen.id),
        "full_name": citizen.full_name,
        "email": citizen.email,
        "phone": citizen.phone,
        "locale": citizen.locale,
        "email_verified": citizen.email_verified_at is not None,
    }


@public_router.post("/citizen/signup", status_code=201)
async def citizen_signup(
    body: CitizenSignupIn,
    request: Request,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    await _rate_limit("citizen_signup", _ip(request), limit=5, window_seconds=3600)
    if not body.accept_privacy:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Privacy policy must be accepted")
    taken = (
        await db.execute(select(CitizenUser).where(CitizenUser.email == body.email.lower()))
    ).scalar_one_or_none()
    if taken is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    citizen = CitizenUser(
        email=body.email.lower(),
        phone=body.phone,
        full_name=body.full_name,
        password_hash=hash_password(body.password),
        locale=pick_locale(body.locale),
        privacy_accepted_at=datetime.now(UTC),
    )
    db.add(citizen)
    await db.flush()
    await log_action(
        db, tenant_id=None, user_id=None, action="citizen.signup",
        entity_type="citizen", entity_id=str(citizen.id), ip_address=_ip(request),
    )
    await db.commit()
    background.add_task(_send_citizen_verification, citizen.id, citizen.email, citizen.locale)
    return {"access_token": _citizen_token(citizen.id), "citizen": _citizen_out(citizen)}


@public_router.post("/citizen/login")
async def citizen_login(
    body: CitizenLoginIn, request: Request, db: AsyncSession = Depends(get_db)
):
    await _rate_limit(
        "citizen_login", f"{body.email.lower()}:{_ip(request)}", limit=10, window_seconds=900
    )
    citizen = (
        await db.execute(select(CitizenUser).where(CitizenUser.email == body.email.lower()))
    ).scalar_one_or_none()
    if citizen is None or not verify_password(body.password, citizen.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if not citizen.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled")
    return {"access_token": _citizen_token(citizen.id), "citizen": _citizen_out(citizen)}


@public_router.post("/citizen/verify-email")
async def citizen_verify_email(body: dict, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_purpose_token(str(body.get("token", "")), "citizen_verify")
    except (pyjwt.PyJWTError, ValueError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired link")
    citizen = await db.get(CitizenUser, uuid.UUID(payload["sub"]))
    if citizen is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired link")
    if citizen.email_verified_at is None:
        citizen.email_verified_at = datetime.now(UTC)
        await db.commit()
    return {"verified": True}


@public_router.post("/citizen/resend-verification")
async def citizen_resend_verification(
    request: Request,
    background: BackgroundTasks,
    citizen: CitizenUser = Depends(_current_citizen),
):
    if citizen.email_verified_at is not None:
        return {"sent": False, "already_verified": True}
    await _rate_limit("citizen_resend", str(citizen.id), limit=3, window_seconds=3600)
    background.add_task(_send_citizen_verification, citizen.id, citizen.email, citizen.locale)
    return {"sent": True}


@public_router.get("/citizen/me")
async def citizen_me(citizen: CitizenUser = Depends(_current_citizen)):
    return _citizen_out(citizen)


# ---------- public lawyer directory ----------

@public_router.get("/lawyers")
async def public_lawyers(
    area: str | None = None,
    city: str | None = None,
    language: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    rows = (
        await db.execute(
            select(LawyerProfile, User, Tenant)
            .join(User, User.id == LawyerProfile.user_id)
            .join(Tenant, Tenant.id == LawyerProfile.tenant_id)
            .where(
                LawyerProfile.is_visible.is_(True),
                User.is_active.is_(True),
                Tenant.status == "active",
            )
            .order_by(LawyerProfile.created_at)
            .limit(500)
        )
    ).all()
    result = []
    for profile, user, tenant in rows:
        if area and area not in (profile.practice_areas or []):
            continue
        if city and city.lower() not in [c.lower() for c in profile.cities or []]:
            continue
        if language and language not in (profile.languages or []):
            continue
        result.append(
            {
                "id": str(profile.id),
                "tenant_id": str(tenant.id),
                "full_name": user.full_name,
                "firm_name": tenant.name,
                "bio": profile.bio,
                "practice_areas": profile.practice_areas or [],
                "cities": profile.cities or [],
                "languages": profile.languages or [],
                "photo": profile.photo,
            }
        )
    return result


# ---------- citizen case requests ----------

class CaseRequestIn(BaseModel):
    category: str = "other"
    description: str = Field(min_length=20, max_length=8000)
    city: str | None = Field(default=None, max_length=120)
    urgency: str = "normal"
    directed_tenant_id: uuid.UUID | None = None


def _case_out(case: CaseRequest, firm_name: str | None = None) -> dict:
    return {
        "id": str(case.id),
        "category": case.category,
        "description": case.description,
        "city": case.city,
        "urgency": case.urgency,
        "status": case.status,
        "directed": case.directed_tenant_id is not None,
        "claimed_by": firm_name,
        "claimed_at": case.claimed_at.isoformat() if case.claimed_at else None,
        "closed_reason": case.closed_reason,
        "created_at": case.created_at.isoformat(),
    }


@public_router.post("/citizen/cases", status_code=201)
async def citizen_create_case(
    body: CaseRequestIn,
    request: Request,
    background: BackgroundTasks,
    citizen: CitizenUser = Depends(_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    if citizen.email_verified_at is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Email not verified")
    await _rate_limit("citizen_case", str(citizen.id), limit=5, window_seconds=24 * 3600)
    if body.category not in PRACTICE_AREAS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown category")
    if body.urgency not in ("normal", "urgent"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown urgency")

    directed_tenant = None
    if body.directed_tenant_id is not None:
        directed_tenant = await db.get(Tenant, body.directed_tenant_id)
        if directed_tenant is None or directed_tenant.status != "active":
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Lawyer not found")

    case = CaseRequest(
        citizen_id=citizen.id,
        category=body.category,
        description=body.description,
        city=body.city,
        locale=citizen.locale,
        urgency=body.urgency,
        directed_tenant_id=body.directed_tenant_id,
    )
    db.add(case)
    await db.flush()
    await log_action(
        db, tenant_id=body.directed_tenant_id, user_id=None, action="marketplace.case_create",
        entity_type="case_request", entity_id=str(case.id),
        details={"category": body.category, "urgency": body.urgency},
        ip_address=_ip(request),
    )
    await db.commit()

    if directed_tenant is not None:
        admins = (
            await db.execute(
                select(User).where(
                    User.tenant_id == directed_tenant.id,
                    User.role == "admin",
                    User.is_active.is_(True),
                )
            )
        ).scalars().all()
        for admin in admins:
            loc = pick_locale(admin.locale)
            background.add_task(
                send_email,
                admin.email,
                tr(loc, "case_directed_subject"),
                tr(loc, "case_directed_body", category=case.category,
                   city=case.city or "-", url=f"{settings.public_base_url}/marketplace"),
            )
    return _case_out(case)


@public_router.get("/citizen/cases")
async def citizen_my_cases(
    citizen: CitizenUser = Depends(_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    cases = (
        await db.execute(
            select(CaseRequest)
            .where(CaseRequest.citizen_id == citizen.id)
            .order_by(CaseRequest.created_at.desc())
            .limit(100)
        )
    ).scalars().all()
    result = []
    for case in cases:
        firm = None
        if case.claimed_by_tenant_id:
            tenant = await db.get(Tenant, case.claimed_by_tenant_id)
            firm = tenant.name if tenant else None
        result.append(_case_out(case, firm))
    return result


async def _owned_case(
    db: AsyncSession, citizen: CitizenUser, case_id: uuid.UUID
) -> CaseRequest:
    case = await db.get(CaseRequest, case_id)
    if case is None or case.citizen_id != citizen.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")
    return case


@public_router.post("/citizen/cases/{case_id}/close")
async def citizen_close_case(
    case_id: uuid.UUID,
    citizen: CitizenUser = Depends(_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    case = await _owned_case(db, citizen, case_id)
    if case.status == "converted":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Case already converted")
    case.status = "closed"
    case.closed_reason = "closed_by_citizen"
    await db.commit()
    return {"closed": True}


# ---------- messages (both sides) ----------

def _message_out(m: CaseRequestMessage) -> dict:
    return {
        "id": str(m.id),
        "sender": m.sender,
        "body": m.body,
        "created_at": m.created_at.isoformat(),
    }


@public_router.get("/citizen/cases/{case_id}/messages")
async def citizen_case_messages(
    case_id: uuid.UUID,
    citizen: CitizenUser = Depends(_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    await _owned_case(db, citizen, case_id)
    rows = (
        await db.execute(
            select(CaseRequestMessage)
            .where(CaseRequestMessage.case_request_id == case_id)
            .order_by(CaseRequestMessage.created_at)
            .limit(500)
        )
    ).scalars().all()
    now = datetime.now(UTC)
    for m in rows:
        if m.sender == "lawyer" and m.read_at is None:
            m.read_at = now
    await db.commit()
    return [_message_out(m) for m in rows]


class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


@public_router.post("/citizen/cases/{case_id}/messages", status_code=201)
async def citizen_send_message(
    case_id: uuid.UUID,
    body: MessageIn,
    background: BackgroundTasks,
    citizen: CitizenUser = Depends(_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    case = await _owned_case(db, citizen, case_id)
    if case.status not in ("claimed",):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Messages are available once a lawyer takes the case"
        )
    await _rate_limit("citizen_msg", str(citizen.id), limit=60, window_seconds=24 * 3600)
    message = CaseRequestMessage(
        case_request_id=case.id, sender="citizen", body=body.body.strip()
    )
    db.add(message)
    await db.commit()

    if case.claimed_by_tenant_id:
        admins = (
            await db.execute(
                select(User).where(
                    User.tenant_id == case.claimed_by_tenant_id,
                    User.role == "admin",
                    User.is_active.is_(True),
                )
            )
        ).scalars().all()
        for admin in admins:
            loc = pick_locale(admin.locale)
            background.add_task(
                send_email,
                admin.email,
                tr(loc, "case_message_subject"),
                tr(loc, "case_message_body",
                   url=f"{settings.public_base_url}/marketplace"),
            )
    return _message_out(message)


# ---------- lawyer side ----------

def _profile_out(profile: LawyerProfile | None) -> dict:
    if profile is None:
        return {
            "is_visible": False, "bio": None, "practice_areas": [],
            "cities": [], "languages": [], "photo": None,
        }
    return {
        "is_visible": profile.is_visible,
        "bio": profile.bio,
        "practice_areas": profile.practice_areas or [],
        "cities": profile.cities or [],
        "languages": profile.languages or [],
        "photo": profile.photo,
    }


@router.get("/profile")
async def get_my_profile(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    profile = (
        await db.execute(select(LawyerProfile).where(LawyerProfile.user_id == user.id))
    ).scalar_one_or_none()
    return _profile_out(profile)


class ProfileIn(BaseModel):
    is_visible: bool = False
    bio: str | None = Field(default=None, max_length=4000)
    practice_areas: list[str] = []
    cities: list[str] = []
    languages: list[str] = []
    photo: str | None = None


@router.put("/profile")
async def update_my_profile(
    body: ProfileIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = (
        await db.execute(select(LawyerProfile).where(LawyerProfile.user_id == user.id))
    ).scalar_one_or_none()
    if profile is None:
        profile = LawyerProfile(tenant_id=user.tenant_id, user_id=user.id)
        db.add(profile)
    profile.is_visible = body.is_visible
    profile.bio = body.bio
    profile.practice_areas = [a for a in body.practice_areas if a in PRACTICE_AREAS]
    profile.cities = [c.strip() for c in body.cities if c.strip()][:20]
    profile.languages = [
        loc for loc in body.languages if loc in settings.supported_locales
    ]
    profile.photo = body.photo
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="marketplace.profile_update",
        entity_type="lawyer_profile", details={"visible": body.is_visible},
    )
    await db.commit()
    return _profile_out(profile)


def _masked_name(full_name: str) -> str:
    """'Filan Fisteku' -> 'Filan F.' — identity revealed only after the claim."""
    parts = full_name.split()
    if len(parts) < 2:
        return parts[0] if parts else "?"
    return f"{parts[0]} {parts[-1][0]}."


@router.get("/cases")
async def lawyer_browse_cases(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Open cases: generic ones plus those directed to my tenant."""
    rows = (
        await db.execute(
            select(CaseRequest, CitizenUser)
            .join(CitizenUser, CitizenUser.id == CaseRequest.citizen_id)
            .where(
                CaseRequest.status == "open",
                (CaseRequest.directed_tenant_id.is_(None))
                | (CaseRequest.directed_tenant_id == user.tenant_id),
            )
            .order_by(CaseRequest.created_at.desc())
            .limit(200)
        )
    ).all()
    return [
        {
            **_case_out(case),
            "citizen_name": _masked_name(citizen.full_name),
            "citizen_locale": citizen.locale,
            "directed_to_me": case.directed_tenant_id == user.tenant_id,
        }
        for case, citizen in rows
    ]


@router.get("/cases/mine")
async def lawyer_my_cases(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    rows = (
        await db.execute(
            select(CaseRequest, CitizenUser)
            .join(CitizenUser, CitizenUser.id == CaseRequest.citizen_id)
            .where(CaseRequest.claimed_by_tenant_id == user.tenant_id)
            .order_by(CaseRequest.claimed_at.desc())
            .limit(200)
        )
    ).all()
    return [
        {
            **_case_out(case),
            "citizen_name": citizen.full_name,
            "citizen_email": citizen.email,
            "citizen_phone": citizen.phone,
            "citizen_locale": citizen.locale,
            "intake_request_id": str(case.intake_request_id) if case.intake_request_id else None,
        }
        for case, citizen in rows
    ]


@router.post("/cases/{case_id}/claim")
async def lawyer_claim_case(
    case_id: uuid.UUID,
    background: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Take the case: conflict check + IntakeRequest(source=marketplace)."""
    from app.models import IntakeRequest

    case = await db.get(CaseRequest, case_id)
    if case is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")
    if case.status != "open":
        raise HTTPException(status.HTTP_409_CONFLICT, "Case already taken or closed")
    if case.directed_tenant_id is not None and case.directed_tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")

    citizen = await db.get(CitizenUser, case.citizen_id)
    conflict = await check_conflicts(db, user.tenant_id, [citizen.full_name])

    intake = IntakeRequest(
        tenant_id=user.tenant_id,
        client_name=citizen.full_name,
        client_email=citizen.email,
        client_phone=citizen.phone,
        summary=case.description,
        source="marketplace",
        status="conflict" if conflict["has_conflicts"] else "new",
        conflict_result=conflict,
        tos_accepted_at=citizen.privacy_accepted_at,
    )
    db.add(intake)
    await db.flush()

    case.status = "claimed"
    case.claimed_by_tenant_id = user.tenant_id
    case.claimed_at = datetime.now(UTC)
    case.intake_request_id = intake.id
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="marketplace.case_claim",
        entity_type="case_request", entity_id=str(case.id),
        details={"has_conflicts": conflict["has_conflicts"]},
    )
    await db.commit()

    tenant = await db.get(Tenant, user.tenant_id)
    loc = pick_locale(citizen.locale)
    background.add_task(
        send_email,
        citizen.email,
        tr(loc, "case_claimed_subject"),
        tr(loc, "case_claimed_body", firm=tenant.name,
           url=f"{settings.public_base_url}/rasti-im"),
    )
    return {
        "claimed": True,
        "intake_request_id": str(intake.id),
        "has_conflicts": conflict["has_conflicts"],
    }


@router.post("/cases/{case_id}/report")
async def lawyer_report_case(
    case_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Flag an abusive/spam case: closes it and leaves an audit trail for the
    platform operator."""
    case = await db.get(CaseRequest, case_id)
    if case is None or case.status != "open":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")
    case.status = "closed"
    case.closed_reason = "reported_abuse"
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="marketplace.case_report",
        entity_type="case_request", entity_id=str(case.id),
        details={"citizen_id": str(case.citizen_id)},
    )
    await db.commit()
    return {"reported": True}


async def _tenant_case(
    db: AsyncSession, user: User, case_id: uuid.UUID
) -> CaseRequest:
    case = await db.get(CaseRequest, case_id)
    if case is None or case.claimed_by_tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")
    return case


@router.get("/cases/{case_id}/messages")
async def lawyer_case_messages(
    case_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _tenant_case(db, user, case_id)
    rows = (
        await db.execute(
            select(CaseRequestMessage)
            .where(CaseRequestMessage.case_request_id == case_id)
            .order_by(CaseRequestMessage.created_at)
            .limit(500)
        )
    ).scalars().all()
    now = datetime.now(UTC)
    for m in rows:
        if m.sender == "citizen" and m.read_at is None:
            m.read_at = now
    await db.commit()
    return [_message_out(m) for m in rows]


@router.post("/cases/{case_id}/messages", status_code=201)
async def lawyer_send_message(
    case_id: uuid.UUID,
    body: MessageIn,
    background: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = await _tenant_case(db, user, case_id)
    message = CaseRequestMessage(
        case_request_id=case.id, sender="lawyer", sender_user_id=user.id,
        body=body.body.strip(),
    )
    db.add(message)
    await db.commit()

    citizen = await db.get(CitizenUser, case.citizen_id)
    if citizen is not None:
        loc = pick_locale(citizen.locale)
        background.add_task(
            send_email,
            citizen.email,
            tr(loc, "case_message_subject"),
            tr(loc, "case_message_body", url=f"{settings.public_base_url}/rasti-im"),
        )
    return _message_out(message)
