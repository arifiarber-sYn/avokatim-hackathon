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
import re
import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import redis.asyncio as aioredis
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import String as sa_String
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.i18n import pick_locale, tr
from app.models import (
    CaseRequest,
    CaseRequestMessage,
    CaseReview,
    CitizenUser,
    Jurisdiction,
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
from app.services.notifications import _is_test_recipient, send_email
from app.services.ops_notify import notify_ops
from app.services.sms import send_sms, sms_enabled

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
    # password_hash is None for social-login accounts that never set one —
    # they must use the provider button (or the reset flow to add a password)
    if (
        citizen is None
        or not citizen.password_hash
        or not verify_password(body.password, citizen.password_hash)
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if not citizen.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled")
    return {"access_token": _citizen_token(citizen.id), "citizen": _citizen_out(citizen)}


async def _send_citizen_welcome(email: str, name: str, locale: str) -> None:
    """Thank-you letter after the account is confirmed — the citizen's
    "successful registration" moment (mirrors the lawyers' verified letter)."""
    loc = pick_locale(locale)
    base = settings.public_base_url
    await send_email(
        email,
        tr(loc, "citizen_welcome_subject", name=name),
        tr(loc, "citizen_welcome_body",
           name=name,
           ava_url=f"{base}/ava",
           post_url=f"{base}/posto-rastin",
           dir_url=f"{base}/avokatet",
           docs_url=f"{base}/dokumentet"),
    )


@public_router.post("/citizen/verify-email")
async def citizen_verify_email(
    body: dict, background: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
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
        # First confirmation only: thank-you letter + heads-up to the operator
        # assistant (test/simulation accounts stay silent)
        if not _is_test_recipient(citizen.email):
            background.add_task(
                _send_citizen_welcome, citizen.email, citizen.full_name, citizen.locale
            )
            background.add_task(
                notify_ops, "regjistrim-qytetar",
                f"Qytetar i ri konfirmoi llogarinë: {citizen.full_name}. "
                f"Letra falënderuese iu dërgua automatikisht — s'kërkohet veprim.",
            )
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


# ---------- citizen account (profile + password) ----------

class CitizenUpdateIn(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=200)
    phone: str | None = Field(default=None, max_length=64)
    locale: str | None = None


@public_router.patch("/citizen/me")
async def citizen_update_me(
    body: CitizenUpdateIn,
    citizen: CitizenUser = Depends(_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    if body.full_name is not None:
        citizen.full_name = body.full_name.strip()
    if body.phone is not None:
        citizen.phone = body.phone.strip() or None
    if body.locale is not None:
        citizen.locale = pick_locale(body.locale)
    await db.commit()
    return _citizen_out(citizen)


class CitizenChangePasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


@public_router.post("/citizen/change-password")
async def citizen_change_password(
    body: CitizenChangePasswordIn,
    request: Request,
    citizen: CitizenUser = Depends(_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    await _rate_limit("citizen_pw_change", str(citizen.id), limit=5, window_seconds=3600)
    if not citizen.password_hash or not verify_password(
        body.current_password, citizen.password_hash
    ):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect")
    citizen.password_hash = hash_password(body.new_password)
    await log_action(
        db, tenant_id=None, user_id=None, action="citizen.change_password",
        entity_type="citizen", entity_id=str(citizen.id), ip_address=_ip(request),
    )
    await db.commit()
    return {"changed": True}


async def _send_citizen_reset(citizen_id: uuid.UUID, email: str, locale: str) -> None:
    token = create_purpose_token("citizen_reset", citizen_id, minutes=60)
    url = f"{settings.public_base_url}/kycu?rivendos={token}"
    loc = pick_locale(locale)
    await send_email(
        email, tr(loc, "citizen_reset_subject"), tr(loc, "citizen_reset_body", url=url)
    )


class CitizenForgotPasswordIn(BaseModel):
    email: EmailStr


@public_router.post("/citizen/forgot-password")
async def citizen_forgot_password(
    body: CitizenForgotPasswordIn,
    request: Request,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    await _rate_limit("citizen_pw_forgot", _ip(request), limit=5, window_seconds=3600)
    citizen = (
        await db.execute(select(CitizenUser).where(CitizenUser.email == body.email.lower()))
    ).scalar_one_or_none()
    # Same response whether the email exists or not (no account enumeration)
    if citizen is not None and citizen.is_active:
        background.add_task(_send_citizen_reset, citizen.id, citizen.email, citizen.locale)
    return {"sent": True}


class CitizenResetPasswordIn(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


@public_router.post("/citizen/reset-password")
async def citizen_reset_password(
    body: CitizenResetPasswordIn, request: Request, db: AsyncSession = Depends(get_db)
):
    try:
        payload = decode_purpose_token(body.token, "citizen_reset")
    except (pyjwt.PyJWTError, ValueError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired link")
    citizen = await db.get(CitizenUser, uuid.UUID(payload["sub"]))
    if citizen is None or not citizen.is_active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired link")
    citizen.password_hash = hash_password(body.new_password)
    if citizen.email_verified_at is None:
        # Owning the reset link proves control of the mailbox
        citizen.email_verified_at = datetime.now(UTC)
    await log_action(
        db, tenant_id=None, user_id=None, action="citizen.reset_password",
        entity_type="citizen", entity_id=str(citizen.id), ip_address=_ip(request),
    )
    await db.commit()
    return {"reset": True}


# ---------- public lawyer directory ----------

async def _tenant_ratings(db: AsyncSession) -> dict[uuid.UUID, tuple[float, int]]:
    """tenant_id -> (average rating 1..5 across the three prompts, count)."""
    from sqlalchemy import func

    rows = (
        await db.execute(
            select(
                CaseReview.tenant_id,
                func.avg(
                    (
                        CaseReview.rating_communication
                        + CaseReview.rating_speed
                        + CaseReview.rating_clarity
                    )
                    / 3.0
                ),
                func.count(CaseReview.id),
            ).group_by(CaseReview.tenant_id)
        )
    ).all()
    return {tid: (round(float(avg), 1), int(cnt)) for tid, avg, cnt in rows}


async def _tenant_cases_completed(db: AsyncSession) -> dict[uuid.UUID, int]:
    """tenant_id -> marketplace cases the office actually took on. Evidence-
    based trust signal (ReferU/COUNSEL model): verified platform activity,
    not self-reported claims."""
    from sqlalchemy import func

    rows = (
        await db.execute(
            select(CaseRequest.claimed_by_tenant_id, func.count(CaseRequest.id))
            .where(
                CaseRequest.claimed_by_tenant_id.is_not(None),
                CaseRequest.status.in_(["claimed", "converted", "closed"]),
            )
            .group_by(CaseRequest.claimed_by_tenant_id)
        )
    ).all()
    return {tid: int(cnt) for tid, cnt in rows}


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
                # Trust gate: only OAK-verified lawyers appear publicly
                LawyerProfile.verification_status == "verified",
                User.is_active.is_(True),
                Tenant.status == "active",
                # Notary offices are listed in /noteret, never here
                Tenant.profession == "lawyer",
            )
            # Highlighted directory placement is a paid-plan perk (lpPlanPaid)
            .order_by((Tenant.plan != "trial").desc(), LawyerProfile.created_at)
            .limit(500)
        )
    ).all()
    ratings = await _tenant_ratings(db)
    cases_completed = await _tenant_cases_completed(db)
    current_year = datetime.now(UTC).year
    result = []
    for profile, user, tenant in rows:
        if area and area not in (profile.practice_areas or []):
            continue
        if city and city.lower() not in [c.lower() for c in profile.cities or []]:
            continue
        if language and language not in (profile.languages or []):
            continue
        avg_rating, review_count = ratings.get(tenant.id, (None, 0))
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
                "highlighted": tenant.plan != "trial",
                "verified": True,
                "founder": profile.is_founder,
                "consult_fee_eur": profile.consult_fee_eur,
                "rating": avg_rating,
                "review_count": review_count,
                "booking": profile.booking_enabled,
                "years_experience": (
                    max(0, current_year - profile.career_start_year)
                    if profile.career_start_year
                    else None
                ),
                "cases_completed": cases_completed.get(tenant.id, 0),
                "flat_services": profile.flat_services or [],
            }
        )
    # Within each placement tier, better-rated lawyers surface first
    result.sort(
        key=lambda r: (r["highlighted"], r["rating"] or 0.0, r["review_count"]),
        reverse=True,
    )
    return result


@public_router.get("/lawyers/{profile_id}")
async def public_lawyer_profile(
    profile_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    """Single lawyer profile — the dedicated /avokatet/[id] page. In 2026 the
    directory profile IS the destination (most clients never visit the firm's
    website), so it carries everything: trust signals, reviews, booking."""
    row = (
        await db.execute(
            select(LawyerProfile, User, Tenant)
            .join(User, User.id == LawyerProfile.user_id)
            .join(Tenant, Tenant.id == LawyerProfile.tenant_id)
            .where(
                LawyerProfile.id == profile_id,
                # Same trust gate as the directory list
                LawyerProfile.is_visible.is_(True),
                LawyerProfile.verification_status == "verified",
                User.is_active.is_(True),
                Tenant.status == "active",
                Tenant.profession == "lawyer",
            )
        )
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lawyer not found")
    profile, user, tenant = row

    ratings = await _tenant_ratings(db)
    cases_completed = await _tenant_cases_completed(db)
    avg_rating, review_count = ratings.get(tenant.id, (None, 0))

    # Recent review comments, anonymized ("Filan F.") — service experience
    # only, never legal outcomes (see CaseReview docstring)
    review_rows = (
        await db.execute(
            select(CaseReview, CitizenUser.full_name)
            .join(CitizenUser, CitizenUser.id == CaseReview.citizen_id)
            .where(
                CaseReview.tenant_id == tenant.id,
                CaseReview.comment.is_not(None),
                CaseReview.comment != "",
            )
            .order_by(CaseReview.created_at.desc())
            .limit(10)
        )
    ).all()
    reviews = [
        {
            "author": _masked_name(name),
            "rating": round(
                (r.rating_communication + r.rating_speed + r.rating_clarity) / 3
            ),
            "comment": r.comment,
            "date": r.created_at.isoformat(),
        }
        for r, name in review_rows
    ]

    current_year = datetime.now(UTC).year
    return {
        "id": str(profile.id),
        "tenant_id": str(tenant.id),
        "full_name": user.full_name,
        "firm_name": tenant.name,
        "bio": profile.bio,
        "practice_areas": profile.practice_areas or [],
        "cities": profile.cities or [],
        "languages": profile.languages or [],
        "photo": profile.photo,
        "verified": True,
        "founder": profile.is_founder,
        "consult_fee_eur": profile.consult_fee_eur,
        "rating": avg_rating,
        "review_count": review_count,
        "booking": profile.booking_enabled,
        "years_experience": (
            max(0, current_year - profile.career_start_year)
            if profile.career_start_year
            else None
        ),
        "cases_completed": cases_completed.get(tenant.id, 0),
        "flat_services": profile.flat_services or [],
        "reviews": reviews,
        "member_since": profile.created_at.isoformat(),
    }


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
        # Last state change — the citizen timeline uses it as the "matter
        # opened" / "closed" timestamp (no dedicated columns for those)
        "updated_at": case.updated_at.isoformat() if case.updated_at else None,
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

    # Quality gate: junk posts waste the lawyers' attention (fail-open on LLM)
    from app.services.case_quality import assess_case

    useful, quality_flag = await assess_case(body.description, body.category)
    if not useful:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            tr(pick_locale(citizen.locale), "case_quality_reject"),
        )

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
        quality_flag=quality_flag,
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

    if not _is_test_recipient(citizen.email):
        background.add_task(
            notify_ops, "rast",
            f"Rast i ri në treg: kategoria {body.category}, qyteti {body.city or '-'}, "
            f"urgjenca {body.urgency}"
            + (f", i drejtuar te '{directed_tenant.name}'" if directed_tenant else "")
            + f". Cilësia: {quality_flag or 'ok'}.",
        )
    if directed_tenant is None:
        # Demand->supply matching: alert lawyers whose profile fits the case
        background.add_task(_notify_matching_lawyers, case.id, body.category, body.city)
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
    reviewed_ids = {
        rid
        for (rid,) in (
            await db.execute(
                select(CaseReview.case_request_id).where(CaseReview.citizen_id == citizen.id)
            )
        ).all()
    }
    result = []
    for case in cases:
        firm = None
        if case.claimed_by_tenant_id:
            tenant = await db.get(Tenant, case.claimed_by_tenant_id)
            firm = tenant.name if tenant else None
        result.append(
            {
                **_case_out(case, firm),
                "reviewed": case.id in reviewed_ids,
                "can_review": case.id not in reviewed_ids and _case_reviewable(case),
            }
        )
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


# ---------- client reviews (trust: rate the service, never the outcome) ----------

def _case_reviewable(case: CaseRequest) -> bool:
    """A case can be reviewed once a lawyer handled it and the engagement
    concluded (converted to a matter or closed)."""
    return case.claimed_by_tenant_id is not None and case.status in ("converted", "closed")


class ReviewIn(BaseModel):
    rating_communication: int = Field(ge=1, le=5)
    rating_speed: int = Field(ge=1, le=5)
    rating_clarity: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


def _review_out(review: CaseReview) -> dict:
    return {
        "id": str(review.id),
        "case_request_id": str(review.case_request_id),
        "rating_communication": review.rating_communication,
        "rating_speed": review.rating_speed,
        "rating_clarity": review.rating_clarity,
        "comment": review.comment,
        "created_at": review.created_at.isoformat(),
    }


@public_router.post("/citizen/cases/{case_id}/review", status_code=201)
async def citizen_review_case(
    case_id: uuid.UUID,
    body: ReviewIn,
    request: Request,
    citizen: CitizenUser = Depends(_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    case = await _owned_case(db, citizen, case_id)
    if not _case_reviewable(case):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Reviews open once a lawyer has handled the case and it is concluded",
        )
    existing = (
        await db.execute(select(CaseReview).where(CaseReview.case_request_id == case.id))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Case already reviewed")
    review = CaseReview(
        case_request_id=case.id,
        citizen_id=citizen.id,
        tenant_id=case.claimed_by_tenant_id,
        rating_communication=body.rating_communication,
        rating_speed=body.rating_speed,
        rating_clarity=body.rating_clarity,
        comment=(body.comment or "").strip() or None,
    )
    db.add(review)
    await db.flush()
    await log_action(
        db, tenant_id=case.claimed_by_tenant_id, user_id=None,
        action="marketplace.case_review", entity_type="case_request",
        entity_id=str(case.id), ip_address=_ip(request),
    )
    await db.commit()
    return _review_out(review)


@public_router.get("/citizen/cases/{case_id}/review")
async def citizen_get_review(
    case_id: uuid.UUID,
    citizen: CitizenUser = Depends(_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    case = await _owned_case(db, citizen, case_id)
    review = (
        await db.execute(select(CaseReview).where(CaseReview.case_request_id == case.id))
    ).scalar_one_or_none()
    return {
        "review": _review_out(review) if review else None,
        "can_review": review is None and _case_reviewable(case),
    }


async def _notify_matching_lawyers(
    case_id: uuid.UUID, category: str, city: str | None
) -> None:
    """Push + email to directory lawyers whose practice areas/cities match a
    freshly posted case — the supply side learns about demand instantly
    instead of having to poll the browse list. Own session (background)."""
    from app.database import SessionLocal
    from app.services.push import send_push_to_user

    async with SessionLocal() as db:
        rows = (
            await db.execute(
                select(User, LawyerProfile)
                .join(LawyerProfile, LawyerProfile.user_id == User.id)
                .join(Tenant, Tenant.id == LawyerProfile.tenant_id)
                .where(
                    LawyerProfile.is_visible.is_(True),
                    LawyerProfile.verification_status == "verified",
                    User.is_active.is_(True),
                    Tenant.status == "active",
                    Tenant.profession == "lawyer",
                )
            )
        ).all()
        notified = 0
        for lawyer, profile in rows:
            areas = profile.practice_areas or []
            cities = [c.lower() for c in profile.cities or []]
            if areas and category not in areas:
                continue
            if city and cities and city.lower() not in cities:
                continue
            loc = pick_locale(lawyer.locale)
            subject = tr(loc, "case_match_subject")
            body = tr(loc, "case_match_body", category=category, city=city or "-",
                      url=f"{settings.public_base_url}/marketplace")
            await send_push_to_user(
                db, lawyer.id, title=subject, body=body, url="/marketplace"
            )
            await send_email(lawyer.email, subject, body)
            if sms_enabled() and profile.sms_case_alerts and profile.phone:
                await send_sms(
                    profile.phone,
                    tr(loc, "sms_case_match", category=category, city=city or "-"),
                )
            notified += 1
        logger.info("Case %s: alerted %d matching lawyers", case_id, notified)


# ---------- SOS: urgent help with on-duty lawyer alerts (Phase 3) ----------

class SosIn(BaseModel):
    description: str = Field(min_length=10, max_length=4000)
    city: str | None = Field(default=None, max_length=120)
    # Recording started before/while sending the SOS — attach it so the
    # claiming lawyer arrives with the evidence already in hand
    evidence_session_id: uuid.UUID | None = None


async def _notify_on_duty_lawyers(case_id: uuid.UUID, city: str | None) -> None:
    """Instant push + email to every opted-in duty lawyer. Own session:
    runs as a background task after the request commits."""
    from app.database import SessionLocal
    from app.services.push import send_push_to_user

    async with SessionLocal() as db:
        rows = (
            await db.execute(
                select(User, LawyerProfile)
                .join(LawyerProfile, LawyerProfile.user_id == User.id)
                .join(Tenant, Tenant.id == LawyerProfile.tenant_id)
                .where(
                    LawyerProfile.sos_on_duty.is_(True),
                    LawyerProfile.verification_status == "verified",
                    User.is_active.is_(True),
                    Tenant.status == "active",
                )
            )
        ).all()
        for lawyer, profile in rows:
            loc = pick_locale(lawyer.locale)
            subject = tr(loc, "sos_alert_subject")
            body = tr(loc, "sos_alert_body", city=city or "-",
                      url=f"{settings.public_base_url}/marketplace")
            await send_push_to_user(
                db, lawyer.id, title=subject, body=body, url="/marketplace"
            )
            await send_email(lawyer.email, subject, body)
            if sms_enabled() and profile.sms_case_alerts and profile.phone:
                await send_sms(profile.phone, tr(loc, "sms_sos_alert", city=city or "-"))
        logger.info("SOS %s: alerted %d on-duty lawyers", case_id, len(rows))


@public_router.post("/citizen/sos", status_code=201)
async def citizen_sos(
    body: SosIn,
    request: Request,
    background: BackgroundTasks,
    citizen: CitizenUser = Depends(_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    """Emergency request: needs a citizen account but NOT a verified email
    (emergencies can't wait for an inbox); hard rate limit instead."""
    await _rate_limit("citizen_sos", str(citizen.id), limit=2, window_seconds=24 * 3600)
    case = CaseRequest(
        citizen_id=citizen.id,
        category="other",
        description=body.description,
        city=body.city,
        locale=citizen.locale,
        urgency="sos",
    )
    db.add(case)
    await db.flush()
    if body.evidence_session_id is not None:
        from app.models import EvidenceSession

        session = await db.get(EvidenceSession, body.evidence_session_id)
        if (
            session is not None
            and session.citizen_id == citizen.id
            and session.case_request_id is None
        ):
            session.case_request_id = case.id
    await log_action(
        db, tenant_id=None, user_id=None, action="marketplace.sos_create",
        entity_type="case_request", entity_id=str(case.id),
        details={"city": body.city}, ip_address=_ip(request),
    )
    await db.commit()
    background.add_task(_notify_on_duty_lawyers, case.id, body.city)
    if not _is_test_recipient(citizen.email):
        background.add_task(
            notify_ops, "sos",
            f"SOS nga qytetari ({body.city or 'qytet i panjohur'}): "
            f"{body.description[:300]}",
            True,
        )
    return _case_out(case)


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


# ---------- public platform stats (Phase 4: "access to justice") ----------

@public_router.get("/stats")
async def public_stats(db: AsyncSession = Depends(get_db)):
    """Anonymous aggregate numbers for the landing page and the
    government/OAK pitch. No personal data."""
    from sqlalchemy import func

    from app.models import LegalCorpusChunk, LegalCorpusDoc

    # Must mirror the /lawyers directory filters exactly, otherwise the
    # landing-page count disagrees with what visitors actually see there.
    lawyers = (
        await db.execute(
            select(func.count(LawyerProfile.id))
            .select_from(LawyerProfile)
            .join(User, User.id == LawyerProfile.user_id)
            .join(Tenant, Tenant.id == LawyerProfile.tenant_id)
            .where(
                LawyerProfile.is_visible.is_(True),
                LawyerProfile.verification_status == "verified",
                User.is_active.is_(True),
                Tenant.status == "active",
                Tenant.profession == "lawyer",
            )
        )
    ).scalar_one()
    cases_total = (await db.execute(select(func.count(CaseRequest.id)))).scalar_one()
    cases_taken = (
        await db.execute(
            select(func.count(CaseRequest.id)).where(
                CaseRequest.status.in_(["claimed", "converted"])
            )
        )
    ).scalar_one()
    # Average time from posting to a lawyer claiming, in hours
    avg_seconds = (
        await db.execute(
            select(
                func.avg(
                    func.extract("epoch", CaseRequest.claimed_at - CaseRequest.created_at)
                )
            ).where(CaseRequest.claimed_at.isnot(None))
        )
    ).scalar_one()
    # Unique acts, not documents: the same law exists in up to 5 official
    # language versions, which used to inflate this public number.
    laws = (
        await db.execute(
            select(
                func.count(
                    func.distinct(
                        func.coalesce(
                            LegalCorpusDoc.reference,
                            func.cast(LegalCorpusDoc.id, sa_String),
                        )
                    )
                )
            )
        )
    ).scalar_one()
    chunks = (await db.execute(select(func.count(LegalCorpusChunk.id)))).scalar_one()
    # Licensed notaries from the official ONK registry snapshot — a strong
    # trust number for the landing page while the platform directory grows
    from app.api.public_tools import _load_notaries

    notaries_licensed = len(_load_notaries().get("notaries", []))
    return {
        "lawyers_in_directory": lawyers,
        "cases_posted": cases_total,
        "cases_taken": cases_taken,
        "avg_claim_hours": round(avg_seconds / 3600, 1) if avg_seconds else None,
        "laws_in_corpus": laws,
        "corpus_chunks": chunks,
        "notaries_licensed": notaries_licensed,
    }


# ---------- public Ava (Phase 2): free legal information chat ----------

PUBLIC_AVA_SYSTEM_PROMPT = (
    "Ti je Ava, asistentja publike ligjore e platformës AvokatIM në Kosovë. "
    "Jep INFORMIM ligjor të përgjithshëm për qytetarët — JO këshillë ligjore "
    "të personalizuar. Përgjigju në gjuhën e pyetjes (shqip, serbisht, "
    "turqisht, boshnjakisht, anglisht ose kinezisht). Bazohu në copëzat e "
    "ligjeve të dhëna dhe në parimet e përgjithshme juridike; kur citon ligj, "
    "shëno saktë burimin (p.sh. 'LPK neni 176'). Kur nuk je e sigurt, thuaje "
    "hapur. Shpjego thjesht, pa zhargon të tepërt. Kur çështja kërkon "
    "vlerësim profesional, përfaqësim ose ka afate, rekomandoja qytetarit "
    "butonin 'Më lidh me avokat' për ta postuar rastin te avokatët e "
    "platformës. DALLIMI AVOKAT/NOTER: disa punë në Kosovë i kryen noteri, "
    "jo avokati — shitblerja e paluajtshmërive, testamentet, trashëgimia "
    "jokontestimore, autorizimet/prokurat noteriale, marrëveshjet pasurore "
    "mes bashkëshortëve (solemnizim i detyrueshëm, Ligji 06/L-010 neni 41), "
    "vërtetimi i nënshkrimeve e kopjeve. Kur çështja i takon noterit, "
    "shpjegoja qytetarit cili lloj akti duhet (akt noterial, solemnizim apo "
    "vërtetim), thekso se kërkohet prania fizike me letërnjoftim te noteri, "
    "dhe udhëzoje te faqja /noteret e AvokatIM ku gjen drejtorinë e "
    "noterëve të licencuar, listën e dokumenteve që duhen marrë me vete dhe "
    "tarifën e përafërt. "
    "Mos kërko dhe mos ruaj të dhëna personale të panevojshme."
)

AVA_ANON_DAILY_LIMIT = 5
AVA_CITIZEN_DAILY_LIMIT = 20
AVA_HISTORY_MAX = 8


class AvaAskIn(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    # [{role: "user"|"assistant", content: str}] — client-held, stateless server
    history: list[dict] = []
    # Anonymous visitors send a random session id (kept in localStorage)
    session_id: str | None = Field(default=None, max_length=64)
    # UI locale — picks the corpus language for citations (official gazette
    # texts exist in sq/sr/tr/bs/en; Albanian is always the fallback)
    locale: str | None = Field(default=None, max_length=8)


async def _optional_citizen(
    creds: HTTPAuthorizationCredentials | None = Depends(citizen_bearer),
    db: AsyncSession = Depends(get_db),
) -> CitizenUser | None:
    if creds is None:
        return None
    try:
        payload = pyjwt.decode(creds.credentials, settings.secret_key, algorithms=["HS256"])
        citizen = await db.get(CitizenUser, uuid.UUID(payload["citizen"]))
    except Exception:
        return None
    return citizen if citizen is not None and citizen.is_active else None


def _ava_quota_key(citizen: CitizenUser | None, ip: str, session_id: str | None) -> tuple[str, int]:
    """(redis key, daily limit) for this caller."""
    day = datetime.now(UTC).strftime("%Y%m%d")
    if citizen is not None:
        return f"avokatim:ava:{day}:cit:{citizen.id}", AVA_CITIZEN_DAILY_LIMIT
    return f"avokatim:ava:{day}:anon:{ip}:{session_id or 'nosession'}", AVA_ANON_DAILY_LIMIT


async def _ava_take_quota(key: str, limit: int) -> int:
    """Consume one question; returns remaining (raises 429 when exhausted).
    Fails open if Redis is down."""
    try:
        r = aioredis.from_url(settings.redis_url)
        pipe = r.pipeline()
        pipe.incr(key)
        pipe.expire(key, 24 * 3600)
        count, _ = await pipe.execute()
        await r.aclose()
        used = int(count)
        if used > limit:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "Daily free question limit reached",
            )
        return max(0, limit - used)
    except HTTPException:
        raise
    except Exception:
        logger.warning("Ava quota check unavailable")
        return limit


async def _ava_quota_left(key: str, limit: int) -> int:
    try:
        r = aioredis.from_url(settings.redis_url)
        used = await r.get(key)
        await r.aclose()
        return max(0, limit - int(used or 0))
    except Exception:
        return limit


@public_router.get("/ava/quota")
async def ava_quota(
    request: Request,
    session_id: str | None = None,
    citizen: CitizenUser | None = Depends(_optional_citizen),
):
    key, limit = _ava_quota_key(citizen, _ip(request), session_id)
    return {
        "limit": limit,
        "remaining": await _ava_quota_left(key, limit),
        "is_citizen": citizen is not None,
    }


async def _ava_prepare(
    db: AsyncSession, body: AvaAskIn
) -> tuple[list, list[dict]]:
    """Build the grounded message list + citations for a public question."""
    from app.llm.base import ChatMessage
    from app.services import rag

    jurisdiction = (
        await db.execute(select(Jurisdiction).where(Jurisdiction.code == "XK"))
    ).scalar_one_or_none()

    context_blocks: list[str] = []
    citations: list[dict] = []
    if jurisdiction is not None:
        for hit in await rag.search_corpus(
            db, jurisdiction.id, body.question, language=body.locale
        ):
            label = hit["doc_title"] + (f", {hit['section']}" if hit["section"] else "")
            context_blocks.append(f"[Nga ligji: {label}]\n{hit['text']}")
            citations.append(
                {"type": "law", "title": hit["doc_title"], "section": hit["section"],
                 "reference": hit["reference"]}
            )

    user_content = body.question
    if context_blocks:
        user_content = (
            "BAZA LIGJORE:\n\n" + "\n\n---\n\n".join(context_blocks)
            + f"\n\n=== PYETJA E QYTETARIT ===\n{body.question}"
        )

    messages = [ChatMessage(role="system", content=PUBLIC_AVA_SYSTEM_PROMPT)]
    for m in body.history[-AVA_HISTORY_MAX:]:
        role, content = m.get("role"), str(m.get("content", ""))[:4000]
        if role in ("user", "assistant") and content:
            messages.append(ChatMessage(role=role, content=content))
    messages.append(ChatMessage(role="user", content=user_content))
    return messages, citations


@public_router.post("/ava/ask")
async def ava_ask(
    body: AvaAskIn,
    request: Request,
    citizen: CitizenUser | None = Depends(_optional_citizen),
    db: AsyncSession = Depends(get_db),
):
    """Free public legal-information chat, grounded in the XK legal corpus.
    Stateless: the client holds the history; nothing is persisted."""
    from app.llm import get_provider

    key, limit = _ava_quota_key(citizen, _ip(request), body.session_id)
    remaining = await _ava_take_quota(key, limit)

    messages, citations = await _ava_prepare(db, body)
    provider = get_provider(None)
    try:
        result = await provider.chat(messages)
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
    return {"answer": result.content, "citations": citations, "remaining": remaining}


@public_router.post("/ava/ask-stream")
async def ava_ask_stream(
    body: AvaAskIn,
    request: Request,
    citizen: CitizenUser | None = Depends(_optional_citizen),
):
    """SSE variant so long answers survive proxies (see D-010)."""
    import json as jsonlib

    from fastapi.responses import StreamingResponse

    from app.database import SessionLocal
    from app.llm import get_provider

    key, limit = _ava_quota_key(citizen, _ip(request), body.session_id)
    remaining = await _ava_take_quota(key, limit)

    def sse(event: dict) -> str:
        return f"data: {jsonlib.dumps(event, ensure_ascii=False)}\n\n"

    async def event_stream():
        async with SessionLocal() as db:
            messages, citations = await _ava_prepare(db, body)
        yield sse({"type": "meta", "citations": citations, "remaining": remaining})
        provider = get_provider(None)
        try:
            async for kind, text in provider.chat_stream(messages):
                if kind == "thinking":
                    yield sse({"type": "thinking", "text": text})
                else:
                    yield sse({"type": "delta", "text": text})
        except Exception as exc:
            logger.exception("public ava stream failed")
            yield sse({"type": "error", "detail": str(exc)})
            return
        yield sse({"type": "done"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


class StructureCaseIn(BaseModel):
    # [{role: "user"|"assistant", content: str}] — the Ava conversation so far
    history: list[dict] = Field(min_length=1, max_length=40)


_STRUCTURE_CASE_PROMPT = (
    "Nga biseda e mëposhtme mes një qytetari dhe asistentes ligjore Ava, "
    "përgatit rastin që qytetari do t'ua postojë avokatëve. Shkruaje "
    "përshkrimin në vetën e parë, qartë dhe me faktet kryesore (çfarë ndodhi, "
    "kur, ku, çfarë kërkon qytetari) — pa këshilla ligjore dhe pa tekst të "
    "Avës. Kthe VETËM JSON:\n"
    '{{"category": "civil|criminal|family|commercial|labor|administrative|other", '
    '"description": "përshkrimi i rastit në gjuhën e qytetarit", '
    '"city": "qyteti nëse përmendet, ndryshe null", '
    '"urgency": "normal|urgent"}}\n\n'
    "BISEDA:\n{conversation}"
)


@public_router.post("/ava/structure-case")
async def ava_structure_case(body: StructureCaseIn, request: Request):
    """Turn an Ava conversation into a clean, prefillable case draft
    (category, first-person description, city, urgency) — so cases arriving
    from the assistant are well-structured instead of raw chat fragments."""
    import json as jsonlib
    import re as relib

    from app.llm import get_provider
    from app.llm.base import ChatMessage

    await _rate_limit("ava_structure", _ip(request), limit=10, window_seconds=3600)

    lines = []
    for m in body.history[-AVA_HISTORY_MAX:]:
        role, content = m.get("role"), str(m.get("content", ""))[:4000]
        if role in ("user", "assistant") and content:
            speaker = "QYTETARI" if role == "user" else "AVA"
            lines.append(f"{speaker}: {content}")
    if not lines:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty conversation")

    provider = get_provider(None)
    try:
        result = await provider.chat(
            [ChatMessage(
                role="user",
                content=_STRUCTURE_CASE_PROMPT.format(conversation="\n\n".join(lines)[:12000]),
            )]
        )
        match = relib.search(r"\{.*\}", result.content, flags=relib.DOTALL)
        data = jsonlib.loads(match.group(0)) if match else {}
    except Exception as exc:
        logger.warning("structure-case LLM failed: %s", exc)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Assistant unavailable")

    category = data.get("category")
    urgency = data.get("urgency")
    return {
        "category": category if category in PRACTICE_AREAS else "other",
        "description": str(data.get("description") or "")[:8000],
        "city": (str(data["city"])[:120] if data.get("city") else None),
        "urgency": urgency if urgency in ("normal", "urgent") else "normal",
    }


# ---------- lawyer side ----------

def _profile_out(profile: LawyerProfile | None) -> dict:
    if profile is None:
        return {
            "is_visible": False, "sos_on_duty": False, "bio": None,
            "practice_areas": [], "cities": [], "languages": [], "photo": None,
            "oak_license_no": None, "verification_status": "none",
            "verification_note": None, "consult_fee_eur": None,
            "career_start_year": None, "flat_services": [],
            "phone": None, "sms_case_alerts": False, "is_founder": False,
        }
    return {
        "is_visible": profile.is_visible,
        "sos_on_duty": profile.sos_on_duty,
        "bio": profile.bio,
        "practice_areas": profile.practice_areas or [],
        "cities": profile.cities or [],
        "languages": profile.languages or [],
        "photo": profile.photo,
        "oak_license_no": profile.oak_license_no,
        "verification_status": profile.verification_status,
        "verification_note": profile.verification_note,
        "consult_fee_eur": profile.consult_fee_eur,
        "career_start_year": profile.career_start_year,
        "flat_services": profile.flat_services or [],
        "phone": profile.phone,
        "sms_case_alerts": profile.sms_case_alerts,
        "is_founder": profile.is_founder,
    }


@router.get("/profile")
async def get_my_profile(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    profile = (
        await db.execute(select(LawyerProfile).where(LawyerProfile.user_id == user.id))
    ).scalar_one_or_none()
    return _profile_out(profile)


@router.get("/referral")
async def my_referral(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Lawyer-brings-lawyer program: the tenant's share code and how many
    offices signed up with it. The code is generated lazily on first request."""
    import secrets as _secrets

    tenant = await db.get(Tenant, user.tenant_id)
    if tenant.referral_code is None:
        for _ in range(5):
            code = _secrets.token_hex(4).upper()
            exists = (
                await db.execute(select(Tenant.id).where(Tenant.referral_code == code))
            ).scalar_one_or_none()
            if exists is None:
                tenant.referral_code = code
                break
        await db.commit()
    referred = (
        await db.execute(
            select(func.count(Tenant.id)).where(
                Tenant.referred_by_code == tenant.referral_code
            )
        )
    ).scalar_one()
    return {
        "code": tenant.referral_code,
        "url": f"{settings.public_base_url}/regjistrohu?ref={tenant.referral_code}",
        "referred_count": referred,
    }


# Public bios must stay professional prose: lawyers sometimes paste raw
# registry rows (personal email, mobile, even date of birth) which then leak
# on the public directory. Any line containing such data is dropped.
_BIO_SCRUB_RES = [
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),  # email address
    re.compile(r"(?:\+|00)\d[\d\s/.\-()]{6,}"),  # international phone
    re.compile(r"(?<!\d)0\d{2}[\s/.\-]{0,3}\d{3}[\s/.\-]{0,3}\d{3,4}(?!\d)"),  # local mobile
    re.compile(r"(?<!\d)\d{1,2}[./-]\d{1,2}[./-](?:19|20)\d{2}(?!\d)"),  # birth date
]


def _scrub_bio(bio: str | None) -> str | None:
    if not bio:
        return None
    kept = [
        line
        for line in bio.splitlines()
        if not any(rx.search(line) for rx in _BIO_SCRUB_RES)
    ]
    return "\n".join(kept).strip() or None


class FlatServiceIn(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    price_eur: int = Field(ge=1, le=10000)


class ProfileIn(BaseModel):
    is_visible: bool = False
    sos_on_duty: bool = False
    bio: str | None = Field(default=None, max_length=4000)
    practice_areas: list[str] = []
    cities: list[str] = []
    languages: list[str] = []
    photo: str | None = None
    oak_license_no: str | None = Field(default=None, max_length=64)
    consult_fee_eur: int | None = Field(default=None, ge=0, le=10000)
    career_start_year: int | None = Field(default=None, ge=1950, le=2100)
    phone: str | None = Field(default=None, max_length=64)
    sms_case_alerts: bool = False
    flat_services: list[FlatServiceIn] = Field(default=[], max_length=10)


@router.put("/profile")
async def update_my_profile(
    body: ProfileIn,
    background: BackgroundTasks,
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
    profile.sos_on_duty = body.sos_on_duty
    profile.bio = _scrub_bio(body.bio)
    profile.practice_areas = [a for a in body.practice_areas if a in PRACTICE_AREAS]
    profile.cities = [c.strip() for c in body.cities if c.strip()][:20]
    profile.languages = [
        loc for loc in body.languages if loc in settings.supported_locales
    ]
    profile.photo = body.photo
    profile.consult_fee_eur = body.consult_fee_eur
    profile.career_start_year = (
        body.career_start_year
        if body.career_start_year and body.career_start_year <= datetime.now(UTC).year
        else None
    )
    profile.phone = (body.phone or "").strip() or None
    profile.sms_case_alerts = body.sms_case_alerts
    profile.flat_services = [
        {"title": s.title.strip(), "price_eur": s.price_eur}
        for s in body.flat_services
        if s.title.strip()
    ][:10]

    # Entering or changing the license number (re)starts verification; the
    # status itself is never client-writable. Auto-approval happens only when
    # the confirmed signup email matches the public chamber registry
    # (services/license_verify.py); otherwise the operator checks by hand.
    new_license = (body.oak_license_no or "").strip() or None
    if new_license != profile.oak_license_no:
        profile.oak_license_no = new_license
        profile.verified_at = None
        profile.verification_note = None
        profile.verification_status = "pending" if new_license else "none"
        # Simulation accounts (test emails) must not ping the operator —
        # their tenants are deleted at cleanup, so there is nothing to verify
        if new_license and not _is_test_recipient(user.email):
            background.add_task(_auto_verify_or_notify, user.id, user.full_name, new_license)

    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="marketplace.profile_update",
        entity_type="lawyer_profile", details={"visible": body.is_visible},
    )
    await db.commit()
    return _profile_out(profile)


async def _auto_verify_or_notify(user_id, lawyer_name: str, license_no: str) -> None:
    """Try the automatic registry check first; if it can't approve safely,
    fall back to pinging the operator for a manual review."""
    from app.services.license_verify import try_auto_verify

    try:
        if await try_auto_verify(user_id):
            return
    except Exception:
        logger.exception("Auto-verify failed for %s — falling back to manual", lawyer_name)
    await _notify_operator_verification(lawyer_name, license_no)
    await notify_ops(
        "verifikim",
        f"{lawyer_name} dërgoi licencën nr. {license_no} — auto-verifikimi nuk "
        f"e kapi (emaili s'përputhet me regjistrin publik), duhet kontroll "
        f"manual te {settings.public_base_url}/platform",
    )


async def _notify_operator_verification(lawyer_name: str, license_no: str) -> None:
    """Tell the platform operator (superadmin) a verification is waiting."""
    from app.database import SessionLocal

    async with SessionLocal() as db:
        operators = (
            await db.execute(
                select(User).where(User.is_superadmin.is_(True), User.is_active.is_(True))
            )
        ).scalars().all()
        for op in operators:
            await send_email(
                op.email,
                "AvokatIM — Verifikim OAK në pritje",
                f"{lawyer_name} dërgoi licencën OAK nr. {license_no} për verifikim.\n"
                f"Kontrolloje në regjistrin publik të OAK dhe aprovoje te "
                f"{settings.public_base_url}/platform",
            )


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
    """Open cases: generic ones plus those directed to my tenant, ranked so
    the best demand/supply matches surface first: SOS, directed to me,
    my practice areas + cities, then recency."""
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

    profile = (
        await db.execute(select(LawyerProfile).where(LawyerProfile.user_id == user.id))
    ).scalar_one_or_none()
    my_areas = set(profile.practice_areas or []) if profile else set()
    my_cities = {c.lower() for c in (profile.cities or [])} if profile else set()

    def match_score(case: CaseRequest) -> int:
        score = 0
        if case.category in my_areas:
            score += 2
        if case.city and case.city.lower() in my_cities:
            score += 1
        return score

    ranked = sorted(
        rows,
        key=lambda pair: (
            pair[0].urgency == "sos",
            pair[0].directed_tenant_id == user.tenant_id,
            match_score(pair[0]),
            pair[0].created_at,
        ),
        reverse=True,
    )
    return [
        {
            **_case_out(case),
            "citizen_name": _masked_name(citizen.full_name),
            "citizen_locale": citizen.locale,
            "directed_to_me": case.directed_tenant_id == user.tenant_id,
            "matches_profile": match_score(case) > 0,
        }
        for case, citizen in ranked
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


# Revenue model (Phase 4, D-008: billing stays manual): the free/trial plan
# gets a monthly lead allowance; paid plans (solo/firm) claim without limits.
# The platform operator changes plans in the /platform panel.
TRIAL_MONTHLY_LEAD_LIMIT = 5


async def _lead_quota(db: AsyncSession, tenant: Tenant) -> dict:
    from sqlalchemy import func

    if tenant.plan != "trial":
        return {"plan": tenant.plan, "limit": None, "used": None, "remaining": None}
    month_start = datetime.now(UTC).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    used = (
        await db.execute(
            select(func.count(CaseRequest.id)).where(
                CaseRequest.claimed_by_tenant_id == tenant.id,
                CaseRequest.claimed_at >= month_start,
            )
        )
    ).scalar_one()
    return {
        "plan": tenant.plan,
        "limit": TRIAL_MONTHLY_LEAD_LIMIT,
        "used": used,
        "remaining": max(0, TRIAL_MONTHLY_LEAD_LIMIT - used),
    }


@router.get("/lead-quota")
async def lead_quota(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    from app.services.platform_billing import has_past_due

    tenant = await db.get(Tenant, user.tenant_id)
    quota = await _lead_quota(db, tenant)
    quota["past_due"] = await has_past_due(db, tenant.id)
    return quota


@router.post("/cases/{case_id}/claim")
async def lawyer_claim_case(
    case_id: uuid.UUID,
    background: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Take the case: conflict check + IntakeRequest(source=marketplace)."""
    from app.models import IntakeRequest
    from app.services.platform_billing import has_past_due

    # Trust gate: only OAK-verified lawyers may take citizen cases
    profile = (
        await db.execute(select(LawyerProfile).where(LawyerProfile.user_id == user.id))
    ).scalar_one_or_none()
    if profile is None or profile.verification_status != "verified":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "OAK license verification required before claiming cases",
        )

    tenant = await db.get(Tenant, user.tenant_id)
    # Notaries are impartial public officers — competing for cases would
    # conflict with their duty, so the marketplace is lawyers-only
    if tenant.profession == "notary":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "The case marketplace is for law offices only"
        )
    quota = await _lead_quota(db, tenant)
    if quota["remaining"] == 0:
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            "Monthly lead limit reached — upgrade your plan",
        )
    # Dunning: an unpaid subscription invoice past due+grace pauses new
    # leads (the lawyer keeps full access to their own matters and data)
    if await has_past_due(db, tenant.id):
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            "Subscription invoice overdue — settle it in Settings to keep claiming",
        )

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


# ---------- SOS video/audio room (Phase 3, LiveKit) ----------
# Both sides of a claimed case can request a join token for the same room.
# Disabled (enabled=false) until LIVEKIT_API_KEY/SECRET are configured.

CALLABLE_STATUSES = ("claimed", "converted")


def _call_response(case: CaseRequest, token: str | None, identity: str) -> dict:
    from app.services.livekit import livekit_enabled, sos_room_name

    return {
        "enabled": livekit_enabled(),
        "room": sos_room_name(case.id),
        "token": token,
        "identity": identity,
        # Empty url = the client derives ws(s):// from its own host
        "url": settings.livekit_url or None,
    }


@router.post("/cases/{case_id}/call-token")
async def lawyer_call_token(
    case_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.livekit import room_token, sos_room_name

    case = await _tenant_case(db, user, case_id)
    if case.status not in CALLABLE_STATUSES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Case is not active")
    identity = f"lawyer-{user.id}"
    token = room_token(sos_room_name(case.id), identity, user.full_name)
    if token is not None:
        await log_action(
            db, tenant_id=user.tenant_id, user_id=user.id,
            action="marketplace.call_join", entity_type="case_request",
            entity_id=str(case.id), details={"side": "lawyer"},
            ip_address=_ip(request),
        )
        await db.commit()
    return _call_response(case, token, identity)


@public_router.post("/citizen/cases/{case_id}/call-token")
async def citizen_call_token(
    case_id: uuid.UUID,
    request: Request,
    citizen: CitizenUser = Depends(_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    from app.services.livekit import room_token, sos_room_name

    case = await _owned_case(db, citizen, case_id)
    if case.status not in CALLABLE_STATUSES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Calls are available once a lawyer takes the case"
        )
    identity = f"citizen-{citizen.id}"
    token = room_token(sos_room_name(case.id), identity, citizen.full_name)
    if token is not None:
        await log_action(
            db, tenant_id=None, user_id=None,
            action="marketplace.call_join", entity_type="case_request",
            entity_id=str(case.id), details={"side": "citizen"},
            ip_address=_ip(request),
        )
        await db.commit()
    return _call_response(case, token, identity)
