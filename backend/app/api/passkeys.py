"""WebAuthn passkeys (D-054 F5): registration from Settings, passwordless
login from the login page. A passkey is possession + biometric/PIN, so a
passkey login skips the TOTP step (standard practice — it is already MFA)."""
import json
import logging
import uuid
from datetime import UTC, datetime
from urllib.parse import urlparse

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.jurisdictions import profile_for
from app.models import PasskeyCredential, Tenant, User
from app.schemas.auth import TokenResponse
from app.security import create_access_token
from app.services.audit import log_action

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/passkeys", tags=["passkeys"])

CHALLENGE_TTL = 300


def _rp_id() -> str:
    if settings.webauthn_rp_id:
        return settings.webauthn_rp_id
    return urlparse(settings.public_base_url).hostname or "localhost"


def _origins() -> list[str]:
    origins = {settings.public_base_url.rstrip("/")}
    for extra in settings.webauthn_extra_origins.split(","):
        extra = extra.strip().rstrip("/")
        if extra:
            origins.add(extra)
    return list(origins)


def _redis() -> aioredis.Redis:
    return aioredis.from_url(settings.redis_url)


async def _user_credentials(db: AsyncSession, user_id: uuid.UUID) -> list[PasskeyCredential]:
    return (
        (
            await db.execute(
                select(PasskeyCredential).where(PasskeyCredential.user_id == user_id)
            )
        )
        .scalars()
        .all()
    )


# ---------- registration (authenticated) ----------

@router.post("/register-options")
async def register_options(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await _user_credentials(db, user.id)
    tenant = await db.get(Tenant, user.tenant_id)
    options = generate_registration_options(
        rp_id=_rp_id(),
        rp_name=profile_for(tenant.country if tenant else None).brand_name,
        user_id=user.id.bytes,
        user_name=user.email,
        user_display_name=user.full_name,
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(c.credential_id))
            for c in existing
        ],
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )
    r = _redis()
    await r.set(f"pk:reg:{user.id}", bytes_to_base64url(options.challenge), ex=CHALLENGE_TTL)
    await r.aclose()
    return json.loads(options_to_json(options))


class RegisterIn(BaseModel):
    credential: dict
    name: str | None = None


@router.post("/register", status_code=201)
async def register(
    body: RegisterIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    r = _redis()
    challenge = await r.get(f"pk:reg:{user.id}")
    await r.delete(f"pk:reg:{user.id}")
    await r.aclose()
    if not challenge:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Challenge expired — retry")
    try:
        verification = verify_registration_response(
            credential=body.credential,
            expected_challenge=base64url_to_bytes(challenge.decode()),
            expected_rp_id=_rp_id(),
            expected_origin=_origins(),
        )
    except Exception as exc:
        logger.warning("Passkey registration failed for %s: %s", user.email, exc)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Passkey verification failed")

    cred = PasskeyCredential(
        tenant_id=user.tenant_id,
        user_id=user.id,
        credential_id=bytes_to_base64url(verification.credential_id),
        public_key=bytes_to_base64url(verification.credential_public_key),
        sign_count=verification.sign_count,
        name=(body.name or f"Passkey {datetime.now(UTC):%d.%m.%Y}")[:120],
    )
    db.add(cred)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="auth.passkey_register",
        entity_type="passkey", entity_id=cred.credential_id[:36],
    )
    await db.commit()
    return {"id": str(cred.id), "name": cred.name}


@router.get("")
async def list_passkeys(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    creds = await _user_credentials(db, user.id)
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "created_at": c.created_at,
            "last_used_at": c.last_used_at,
        }
        for c in creds
    ]


@router.delete("/{passkey_id}", status_code=204)
async def delete_passkey(
    passkey_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cred = await db.get(PasskeyCredential, passkey_id)
    if cred is None or cred.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Passkey not found")
    await db.delete(cred)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="auth.passkey_delete",
        entity_type="passkey", entity_id=str(passkey_id),
    )
    await db.commit()


# ---------- login (public) ----------

class LoginOptionsIn(BaseModel):
    email: str


@router.post("/login-options")
async def login_options(body: LoginOptionsIn, db: AsyncSession = Depends(get_db)):
    email = body.email.lower().strip()
    user = (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    creds = await _user_credentials(db, user.id) if user else []
    # Same response shape whether or not the account exists (no enumeration);
    # with no allowed credentials the browser prompt simply fails.
    options = generate_authentication_options(
        rp_id=_rp_id(),
        allow_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(c.credential_id))
            for c in creds
        ],
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    r = _redis()
    await r.set(f"pk:auth:{email}", bytes_to_base64url(options.challenge), ex=CHALLENGE_TTL)
    await r.aclose()
    return json.loads(options_to_json(options))


class LoginIn(BaseModel):
    email: str
    credential: dict


@router.post("/login", response_model=TokenResponse)
async def login_with_passkey(body: LoginIn, db: AsyncSession = Depends(get_db)):
    email = body.email.lower().strip()
    r = _redis()
    challenge = await r.get(f"pk:auth:{email}")
    await r.delete(f"pk:auth:{email}")
    await r.aclose()
    if not challenge:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Challenge expired — retry")

    user = (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    raw_id = body.credential.get("id")
    cred = (
        await db.execute(
            select(PasskeyCredential).where(
                PasskeyCredential.user_id == user.id,
                PasskeyCredential.credential_id == raw_id,
            )
        )
    ).scalar_one_or_none()
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    try:
        verification = verify_authentication_response(
            credential=body.credential,
            expected_challenge=base64url_to_bytes(challenge.decode()),
            expected_rp_id=_rp_id(),
            expected_origin=_origins(),
            credential_public_key=base64url_to_bytes(cred.public_key),
            credential_current_sign_count=cred.sign_count,
        )
    except Exception as exc:
        logger.warning("Passkey login failed for %s: %s", email, exc)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    tenant = await db.get(Tenant, user.tenant_id)
    if tenant is not None and tenant.status == "suspended" and not user.is_superadmin:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Tenant suspended — contact the platform operator"
        )

    cred.sign_count = verification.new_sign_count
    cred.last_used_at = datetime.now(UTC)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="auth.login_passkey",
    )
    await db.commit()
    # Passkey = possession + user verification → already MFA, no TOTP step
    return TokenResponse(
        access_token=create_access_token(user.id, user.tenant_id, token_version=user.token_version)
    )
