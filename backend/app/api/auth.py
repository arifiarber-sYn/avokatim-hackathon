import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import bearer, get_current_user
from app.models import Tenant, User
from app.schemas.auth import (
    ProfileUpdateRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    TwoFASetupResponse,
    TwoFAVerifyRequest,
    UserOut,
)
from app.security import (
    create_access_token,
    decode_token,
    hash_password,
    new_totp_secret,
    totp_uri,
    verify_password,
    verify_totp,
)
from app.services.audit import log_action

router = APIRouter(prefix="/auth", tags=["auth"])


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


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    user = (
        await db.execute(select(User).where(User.email == body.email.lower()))
    ).scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled")

    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="auth.login",
        ip_address=request.client.host if request.client else None,
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
async def me(user: User = Depends(get_current_user)):
    return user


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
