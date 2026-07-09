"""FastAPI dependencies: current user, tenant scoping."""
import uuid
from datetime import UTC, datetime

import jwt as pyjwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Tenant, User
from app.security import decode_token

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = decode_token(creds.credentials)
    except pyjwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    if payload.get("pre_2fa"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "2FA verification required")
    user = await db.get(User, uuid.UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
    # The tenant claim must match the user's actual tenant.
    if payload.get("tenant") and payload["tenant"] != str(user.tenant_id):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token/tenant mismatch")

    tenant = await db.get(Tenant, user.tenant_id)
    if tenant is not None and not user.is_superadmin:
        if tenant.status == "suspended":
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Tenant suspended — contact the platform operator"
            )
        if (
            tenant.plan == "trial"
            and tenant.trial_ends_at is not None
            and tenant.trial_ends_at < datetime.now(UTC)
        ):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Trial expired")
        # Firm 2FA policy: members without TOTP may only reach /api/auth
        # (so they can still log in and enable it).
        if (
            tenant.require_2fa
            and not user.totp_enabled
            and not request.url.path.startswith("/api/auth")
        ):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "2FA required by firm policy")
    return user


def require_superadmin(user: User = Depends(get_current_user)) -> User:
    if not user.is_superadmin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Platform operator only")
    return user
