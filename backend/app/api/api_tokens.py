"""Personal access tokens for the public API (Settings -> Integrations).

The plaintext token is returned exactly once, on creation. Each user manages
only their own tokens; creation and revocation are audit-logged.
"""
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models import ApiToken, User
from app.services import api_tokens as svc
from app.services.audit import log_action

router = APIRouter(prefix="/api-tokens", tags=["api-tokens"])


class TokenCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    scope: str = Field(default="read", pattern="^(read|read_write)$")


def _row(t: ApiToken) -> dict:
    return {
        "id": str(t.id),
        "name": t.name,
        "prefix": t.prefix,
        "scope": t.scope,
        "created_at": t.created_at,
        "last_used_at": t.last_used_at,
        "revoked_at": t.revoked_at,
    }


@router.get("")
async def list_tokens(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    rows = (
        (
            await db.execute(
                select(ApiToken)
                .where(ApiToken.user_id == user.id)
                .order_by(ApiToken.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return [_row(t) for t in rows]


@router.post("", status_code=201)
async def create_token(
    body: TokenCreateIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    active = [
        t
        for t in (
            await db.execute(select(ApiToken).where(ApiToken.user_id == user.id))
        ).scalars()
        if t.revoked_at is None
    ]
    if len(active) >= svc.MAX_ACTIVE_TOKENS_PER_USER:
        raise HTTPException(400, "Token limit reached — revoke an unused token first")

    plaintext = svc.generate_token()
    token = ApiToken(
        tenant_id=user.tenant_id,
        user_id=user.id,
        name=body.name.strip(),
        token_hash=svc.hash_token(plaintext),
        prefix=svc.display_prefix(plaintext),
        scope=body.scope,
    )
    db.add(token)
    await db.flush()
    await log_action(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        action="api_token.create",
        entity_type="api_token",
        entity_id=str(token.id),
        details={"name": token.name, "scope": token.scope, "prefix": token.prefix},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    # The only moment the plaintext ever leaves the server.
    return {**_row(token), "token": plaintext}


@router.delete("/{token_id}")
async def revoke_token(
    token_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    token = (
        await db.execute(
            select(ApiToken).where(
                ApiToken.id == token_id, ApiToken.user_id == user.id
            )
        )
    ).scalar_one_or_none()
    if token is None:
        raise HTTPException(404, "Token not found")
    if token.revoked_at is None:
        token.revoked_at = datetime.now(UTC)
        await log_action(
            db,
            tenant_id=user.tenant_id,
            user_id=user.id,
            action="api_token.revoke",
            entity_type="api_token",
            entity_id=str(token.id),
            details={"name": token.name, "prefix": token.prefix},
            ip_address=request.client.host if request.client else None,
        )
        await db.commit()
    return {"revoked": True}
