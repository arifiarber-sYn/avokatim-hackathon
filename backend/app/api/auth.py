import logging
import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import redis.asyncio as aioredis
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.deps import bearer, get_current_user
from app.models import Tenant, User
from app.schemas.auth import (
    AcceptInviteRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    ProfileUpdateRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse,
    TwoFASetupResponse,
    TwoFAVerifyRequest,
    UserOut,
    VerifyEmailRequest,
)
from app.security import (
    create_access_token,
    create_purpose_token,
    decode_purpose_token,
    decode_token,
    hash_password,
    new_totp_secret,
    password_fingerprint,
    totp_uri,
    verify_password,
    verify_totp,
)
from app.services.audit import log_action
from app.services.notifications import send_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# 3 free months (the ICL-pilot promise); after that a paid plan is required
from app.services.platform_billing import TRIAL_DAYS  # noqa: E402  (=90)
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 15 * 60


async def _check_login_rate_limit(email: str, ip: str | None) -> None:
    """Sliding lockout: max LOGIN_MAX_ATTEMPTS failed tries per email+IP window."""
    try:
        r = aioredis.from_url(settings.redis_url)
        key = f"avokatim:login_fail:{email}:{ip or 'noip'}"
        count = await r.get(key)
        await r.aclose()
        if count is not None and int(count) >= LOGIN_MAX_ATTEMPTS:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "Too many failed attempts — try again in 15 minutes",
            )
    except HTTPException:
        raise
    except Exception:  # Redis down must never lock everyone out
        logger.warning("Login rate-limit check unavailable")


async def _record_login_failure(email: str, ip: str | None) -> None:
    try:
        r = aioredis.from_url(settings.redis_url)
        key = f"avokatim:login_fail:{email}:{ip or 'noip'}"
        pipe = r.pipeline()
        pipe.incr(key)
        pipe.expire(key, LOGIN_WINDOW_SECONDS)
        await pipe.execute()
        await r.aclose()
    except Exception:
        pass


def _user_out(user: User, tenant: Tenant | None) -> UserOut:
    out = UserOut.model_validate(user)
    out.email_verified = user.email_verified_at is not None
    if tenant is not None:
        out.tenant_plan = tenant.plan
        out.tenant_status = tenant.status
        out.tenant_trial_ends_at = (
            tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None
        )
        out.tenant_require_2fa = tenant.require_2fa
        out.tenant_profession = tenant.profession
    return out


async def _send_verification_email(user_id: uuid.UUID, email: str, locale: str) -> None:
    from app.i18n import pick_locale, tr

    loc = pick_locale(locale)
    token = create_purpose_token("verify_email", user_id, minutes=60 * 24 * 3)
    url = f"{settings.public_base_url}/verifiko-email?token={token}"
    await send_email(
        email,
        tr(loc, "lawyer_verify_subject"),
        tr(loc, "lawyer_verify_body", url=url),
    )


async def _send_welcome_email(
    email: str, name: str, locale: str, profession: str = "lawyer"
) -> None:
    """Welcome email with the concrete next steps (activate public profile,
    add the license) — the onboarding gap seen with the first real signups.
    Notary offices get their own variant (no OAK, no marketplace)."""
    from app.i18n import pick_locale, tr

    loc = pick_locale(locale)
    key = "notary_welcome" if profession == "notary" else "lawyer_welcome"
    await send_email(
        email,
        tr(loc, f"{key}_subject", name=name),
        tr(
            loc,
            f"{key}_body",
            onboarding_url=f"{settings.public_base_url}/onboarding",
            trial_days=TRIAL_DAYS,
            contact_url=f"{settings.public_base_url}/kontakti",
        ),
    )


@router.get("/setup-needed")
async def setup_needed(db: AsyncSession = Depends(get_db)) -> dict:
    """True until the first account exists — drives the first-run setup screen."""
    count = (await db.execute(select(func.count(User.id)))).scalar_one()
    return {"setup_needed": count == 0}


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(func.count(User.id)))).scalar_one()
    if existing > 0:
        # Self-hosted single practice: after first-run, new users are invited
        # by the admin, not self-registered.
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Setup already completed")

    tenant = Tenant(name=body.practice_name, kind="solo", default_locale=body.locale)
    db.add(tenant)
    await db.flush()
    user = User(
        tenant_id=tenant.id,
        email=body.email.lower(),
        full_name=body.full_name,
        password_hash=hash_password(body.password),
        role="admin",
        locale=body.locale,
    )
    db.add(user)
    await db.flush()
    await log_action(
        db, tenant_id=tenant.id, user_id=user.id, action="auth.register",
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return TokenResponse(access_token=create_access_token(user.id, tenant.id))


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    body: SignupRequest,
    request: Request,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Public self-service signup: new law practice on a 30-day trial."""
    taken = (
        await db.execute(select(User).where(User.email == body.email.lower()))
    ).scalar_one_or_none()
    if taken is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    if not body.accept_tos:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Terms of service must be accepted"
        )

    # Referral program: record who brought this office (only valid codes)
    referred_by = None
    if body.referral_code:
        referrer = (
            await db.execute(
                select(Tenant).where(Tenant.referral_code == body.referral_code.strip().upper())
            )
        ).scalar_one_or_none()
        if referrer is not None:
            referred_by = referrer.referral_code

    tenant = Tenant(
        name=body.practice_name,
        kind="solo",
        profession=body.profession,
        default_locale=body.locale,
        plan="trial",
        status="active",
        seats_limit=3,
        trial_ends_at=datetime.now(UTC) + timedelta(days=TRIAL_DAYS),
        tos_accepted_at=datetime.now(UTC),
        referred_by_code=referred_by,
    )
    db.add(tenant)
    await db.flush()
    user = User(
        tenant_id=tenant.id,
        email=body.email.lower(),
        full_name=body.full_name,
        password_hash=hash_password(body.password),
        role="admin",
        locale=body.locale,
    )
    db.add(user)
    await db.flush()
    await log_action(
        db, tenant_id=tenant.id, user_id=user.id, action="auth.signup",
        details={
            **({"referred_by": referred_by} if referred_by else {}),
            "profession": body.profession,
        },
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    background.add_task(_send_verification_email, user.id, user.email, body.locale)
    background.add_task(
        _send_welcome_email, user.email, user.full_name, body.locale, body.profession
    )
    return TokenResponse(access_token=create_access_token(user.id, tenant.id))


@router.post("/verify-email")
async def verify_email(body: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_purpose_token(body.token, "verify_email")
    except (pyjwt.PyJWTError, ValueError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired link")
    user = await db.get(User, uuid.UUID(payload["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired link")
    if user.email_verified_at is None:
        user.email_verified_at = datetime.now(UTC)
        await log_action(
            db, tenant_id=user.tenant_id, user_id=user.id, action="auth.email_verified"
        )
        await db.commit()
    return {"verified": True}


@router.post("/resend-verification")
async def resend_verification(
    background: BackgroundTasks, user: User = Depends(get_current_user)
):
    if user.email_verified_at is not None:
        return {"sent": False, "already_verified": True}
    background.add_task(_send_verification_email, user.id, user.email, user.locale)
    return {"sent": True}


@router.post("/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Always returns 200 to avoid disclosing which emails exist."""
    user = (
        await db.execute(select(User).where(User.email == body.email.lower()))
    ).scalar_one_or_none()
    if user is not None and user.is_active:
        token = create_purpose_token(
            "reset_password", user.id, minutes=60,
            fingerprint=password_fingerprint(user.password_hash),
        )
        url = f"{settings.public_base_url}/rivendos?token={token}"

        async def _send() -> None:
            await send_email(
                user.email,
                "AvokatIM — Rivendos fjalëkalimin / Reset your password",
                "Përshëndetje,\n\nPër të rivendosur fjalëkalimin hape këtë link "
                f"(vlen 1 orë):\n{url}\n\nNëse nuk e kërkove ti, injoroje këtë email.\n\n— AvokatIM",
            )

        background.add_task(_send)
    return {"sent": True}


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_purpose_token(body.token, "reset_password")
    except (pyjwt.PyJWTError, ValueError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired link")
    user = await db.get(User, uuid.UUID(payload["sub"]))
    if user is None or payload.get("fp") != password_fingerprint(user.password_hash):
        # Fingerprint mismatch = token already used or password since changed
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired link")
    user.password_hash = hash_password(body.password)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="auth.password_reset"
    )
    await db.commit()
    return {"reset": True}


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is wrong")
    user.password_hash = hash_password(body.new_password)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="auth.password_changed"
    )
    await db.commit()
    return {"changed": True}


@router.post("/accept-invite", response_model=TokenResponse)
async def accept_invite(body: AcceptInviteRequest, db: AsyncSession = Depends(get_db)):
    """A team member invited by email sets their own password here."""
    try:
        payload = decode_purpose_token(body.token, "invite")
    except (pyjwt.PyJWTError, ValueError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired invite")
    user = await db.get(User, uuid.UUID(payload["sub"]))
    if user is None or payload.get("fp") != password_fingerprint(user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired invite")
    tenant = await db.get(Tenant, user.tenant_id)
    seats_used = (
        await db.execute(
            select(func.count(User.id)).where(
                User.tenant_id == user.tenant_id, User.is_active.is_(True)
            )
        )
    ).scalar_one()
    if tenant is not None and seats_used >= tenant.seats_limit:
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED, "Seat limit reached — ask your admin to upgrade"
        )
    user.password_hash = hash_password(body.password)
    user.is_active = True
    user.email_verified_at = datetime.now(UTC)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="auth.invite_accepted"
    )
    await db.commit()
    return TokenResponse(access_token=create_access_token(user.id, user.tenant_id))


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    ip = request.client.host if request.client else None
    email = body.email.lower()
    await _check_login_rate_limit(email, ip)

    user = (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        await _record_login_failure(email, ip)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled")
    tenant = await db.get(Tenant, user.tenant_id)
    if tenant is not None and tenant.status == "suspended" and not user.is_superadmin:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Tenant suspended — contact the platform operator"
        )

    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="auth.login",
        ip_address=ip,
    )
    await db.commit()

    if user.totp_enabled:
        return TokenResponse(
            access_token=create_access_token(user.id, user.tenant_id, pre_2fa=True),
            requires_2fa=True,
        )
    return TokenResponse(access_token=create_access_token(user.id, user.tenant_id))


@router.post("/2fa/verify", response_model=TokenResponse)
async def verify_2fa(
    body: TwoFAVerifyRequest,
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
):
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = decode_token(creds.credentials)
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    user = await db.get(User, uuid.UUID(payload["sub"]))
    if user is None or not user.totp_secret:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "2FA not configured")
    if not verify_totp(user.totp_secret, body.code):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid 2FA code")
    return TokenResponse(access_token=create_access_token(user.id, user.tenant_id))


@router.post("/2fa/setup", response_model=TwoFASetupResponse)
async def setup_2fa(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    secret = new_totp_secret()
    user.totp_secret = secret
    user.totp_enabled = False
    await db.commit()
    return TwoFASetupResponse(secret=secret, otpauth_uri=totp_uri(secret, user.email))


@router.post("/2fa/enable")
async def enable_2fa(
    body: TwoFAVerifyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.totp_secret or not verify_totp(user.totp_secret, body.code):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid 2FA code")
    user.totp_enabled = True
    await log_action(db, tenant_id=user.tenant_id, user_id=user.id, action="auth.2fa_enabled")
    await db.commit()
    return {"enabled": True}


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    tenant = await db.get(Tenant, user.tenant_id)
    return _user_out(user, tenant)


@router.patch("/me", response_model=UserOut)
async def update_me(
    body: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.full_name is not None:
        user.full_name = body.full_name
    if body.billable_hours_target_monthly is not None:
        user.billable_hours_target_monthly = body.billable_hours_target_monthly
    await db.commit()
    await db.refresh(user)
    return user
