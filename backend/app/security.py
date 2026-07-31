"""Password hashing, JWT tokens and TOTP 2FA."""
import base64
import uuid
from datetime import UTC, datetime, timedelta
from functools import lru_cache

import bcrypt
import jwt
import pyotp
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import settings

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def create_access_token(
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
    *,
    pre_2fa: bool = False,
    token_version: int = 0,
) -> str:
    """pre_2fa tokens are only good for the /auth/2fa/verify step.
    `token_version` must match users.token_version at request time (D-033) —
    bumping the column instantly revokes every outstanding token."""
    now = datetime.now(UTC)
    minutes = 5 if pre_2fa else settings.access_token_minutes
    payload = {
        "sub": str(user_id),
        "tenant": str(tenant_id),
        "pre_2fa": pre_2fa,
        "ver": token_version,
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


# ---------- TOTP secret encryption at rest (D-033) ----------
# Same key material as document storage but a different salt, so the two
# domains cannot decrypt each other. Stored values carry an `enc:v1:` prefix;
# legacy plaintext rows (or a missing key) keep working unchanged.

_TOTP_ENC_PREFIX = "enc:v1:"
_TOTP_SALT = b"avokatim-totp-secrets-v1"


@lru_cache(maxsize=1)
def _totp_fernet() -> Fernet | None:
    if not settings.doc_encryption_key:
        return None
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=_TOTP_SALT, iterations=600_000)
    key = base64.urlsafe_b64encode(kdf.derive(settings.doc_encryption_key.encode()))
    return Fernet(key)


def protect_totp_secret(secret: str) -> str:
    """Encrypt a TOTP secret for DB storage (plaintext if no key configured)."""
    fernet = _totp_fernet()
    if fernet is None:
        return secret
    return _TOTP_ENC_PREFIX + fernet.encrypt(secret.encode()).decode()


def reveal_totp_secret(stored: str) -> str:
    """Decrypt a stored TOTP secret; passes legacy plaintext values through."""
    if not stored.startswith(_TOTP_ENC_PREFIX):
        return stored
    fernet = _totp_fernet()
    if fernet is None:
        raise ValueError("TOTP secret is encrypted but doc_encryption_key is not set")
    try:
        return fernet.decrypt(stored.removeprefix(_TOTP_ENC_PREFIX).encode()).decode()
    except InvalidToken as exc:
        raise ValueError("TOTP secret cannot be decrypted (wrong key?)") from exc


def totp_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=settings.totp_issuer)


def verify_totp(secret: str, code: str) -> bool:
    return pyotp.TOTP(secret).verify(code, valid_window=1)
