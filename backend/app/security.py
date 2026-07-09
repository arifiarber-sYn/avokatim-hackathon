"""Password hashing, JWT tokens and TOTP 2FA."""
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
import pyotp

from app.config import settings

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def create_access_token(user_id: uuid.UUID, tenant_id: uuid.UUID, *, pre_2fa: bool = False) -> str:
    """pre_2fa tokens are only good for the /auth/2fa/verify step."""
    now = datetime.now(UTC)
    minutes = 5 if pre_2fa else settings.access_token_minutes
    payload = {
        "sub": str(user_id),
        "tenant": str(tenant_id),
        "pre_2fa": pre_2fa,
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])


def create_purpose_token(
    purpose: str, user_id: uuid.UUID, *, minutes: int, fingerprint: str = ""
) -> str:
    """Single-purpose signed token (email verification, password reset, team
    invite). `fingerprint` binds the token to mutable state — e.g. a fragment
    of the password hash — so it self-invalidates once that state changes."""
    now = datetime.now(UTC)
    payload = {
        "purpose": purpose,
        "sub": str(user_id),
        "fp": fingerprint,
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_purpose_token(token: str, purpose: str) -> dict:
    """Raises jwt.PyJWTError on invalid/expired; ValueError on wrong purpose."""
    payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    if payload.get("purpose") != purpose:
        raise ValueError("Wrong token purpose")
    return payload


def password_fingerprint(password_hash: str) -> str:
    return password_hash[-16:]


def new_totp_secret() -> str:
    return pyotp.random_base32()


def totp_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=settings.totp_issuer)


def verify_totp(secret: str, code: str) -> bool:
    return pyotp.TOTP(secret).verify(code, valid_window=1)
