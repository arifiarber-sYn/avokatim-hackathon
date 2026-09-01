"""FastAPI dependencies: current user, tenant scoping."""
import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, scope_session_to_tenant
from app.models import ApiToken, Tenant, User
from app.security import decode_token
from app.services import api_tokens as api_token_svc

bearer = HTTPBearer(auto_error=False)

# last_used_at is refreshed at most this often (avoids a write per request)
_LAST_USED_REFRESH = timedelta(minutes=5)


async def _user_from_api_token(
    request: Request, credential: str, db: AsyncSession
) -> User:
    """Resolve an `avk_...` personal access token to its creating user.

    Same tenant checks and RLS pinning as the JWT path; 2FA policy does not
    apply (machine access, created inside an authenticated session) and
    read-scope tokens are rejected on any mutating verb.
    """
    token = (
        await db.execute(
            select(ApiToken).where(
                ApiToken.token_hash == api_token_svc.hash_token(credential)
            )
        )
    ).scalar_one_or_none()
    if token is None or token.revoked_at is not None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or revoked API token")
    if not api_token_svc.scope_allows(token.scope, request.method):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "This API token is read-only"
        )
    user = await db.get(User, token.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")

    now = datetime.now(UTC)
    if token.last_used_at is None or now - token.last_used_at > _LAST_USED_REFRESH:
        token.last_used_at = now
        # Commit BEFORE the RLS SET LOCAL below — committing later would end
        # the transaction that carries the tenant scoping.
        await db.commit()

    if not user.is_superadmin:
        await scope_session_to_tenant(db, user.tenant_id)
    tenant = await db.get(Tenant, user.tenant_id)
    if tenant is not None and not user.is_superadmin:
        if tenant.status == "suspended":
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Tenant suspended — contact the platform operator"
            )
        if (
            tenant.plan == "trial"
            and tenant.trial_ends_at is not None
            and tenant.trial_ends_at < now
        ):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Trial expired")
    return user


async def get_current_user(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    if api_token_svc.is_api_token(creds.credentials):
        return await _user_from_api_token(request, creds.credentials, db)
    try:
        payload = decode_token(creds.credentials)
    except pyjwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    if payload.get("pre_2fa"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "2FA verification required")
    user = await db.get(User, uuid.UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
    # Immediate revocation (D-033): bumping users.token_version kills every
    # token issued before the bump (password reset/change does this).
    if payload.get("ver", 0) != user.token_version:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session revoked — log in again")
    # The tenant claim must match the user's actual tenant.
    if payload.get("tenant") and payload["tenant"] != str(user.tenant_id):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token/tenant mismatch")

    # RLS defense in depth (D-033): pin this DB session to the user's tenant
    # so Postgres itself blocks cross-tenant rows even if a query forgets the
    # tenant filter. Superadmins stay unscoped — /platform reads all tenants.
    if not user.is_superadmin:
        await scope_session_to_tenant(db, user.tenant_id)

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
