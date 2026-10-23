"""Team management inside a tenant: lawyers, staff, admins."""
import secrets
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.jurisdictions import profile_for
from app.models import Tenant, User
from app.schemas.auth import UserOut
from app.security import create_purpose_token, hash_password, password_fingerprint
from app.services.audit import log_action
from app.services.notifications import send_email

router = APIRouter(prefix="/team", tags=["team"])

ROLES = ("admin", "lawyer", "staff")
INVITE_VALID_MINUTES = 60 * 24 * 7  # 7 days


def require_admin(user: User) -> None:
    """Team administration is an admin-only operation (industry standard)."""
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin only")


class TeamInviteIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    role: str = "lawyer"


class TeamMemberUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None


class TeamMemberOut(UserOut):
    is_active: bool
    invite_pending: bool = False


def _member_out(member: User) -> TeamMemberOut:
    out = TeamMemberOut.model_validate(member)
    out.email_verified = member.email_verified_at is not None
    # A member who never activated (invited, hasn't set a password) shows as pending
    out.invite_pending = not member.is_active and member.email_verified_at is None
    return out


@router.get("", response_model=list[TeamMemberOut])
async def list_team(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(User)
        .where(User.tenant_id == user.tenant_id)
        .order_by(User.created_at)
    )
    members = (await db.execute(stmt)).scalars().all()
    return [_member_out(m) for m in members]


async def _send_invite_email(
    email: str, invited_by: str, firm: str, token: str, brand: str = "AvokatIM"
) -> None:
    url = f"{settings.public_base_url}/ftesa?token={token}"
    await send_email(
        email,
        f"{brand} — Ftesë nga {firm}",
        f"Përshëndetje,\n\n{invited_by} të fton të bashkohesh me zyrën \"{firm}\" "
        f"në {brand}.\n\nVendos fjalëkalimin tënd këtu (linku vlen 7 ditë):\n{url}\n\n— {brand}",
    )


@router.post("/invite", response_model=TeamMemberOut, status_code=201)
async def invite_member(
    body: TeamInviteIn,
    background: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Invite by email — the member sets their own password via the link."""
    require_admin(user)
    if body.role not in ROLES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid role")
    existing = (
        await db.execute(select(User).where(User.email == body.email.lower()))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")

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
            status.HTTP_402_PAYMENT_REQUIRED,
            f"Seat limit reached ({tenant.seats_limit}) — upgrade the plan",
        )

    member = User(
        tenant_id=user.tenant_id,
        email=body.email.lower(),
        full_name=body.full_name,
        # Unusable random password until the invite is accepted
        password_hash=hash_password(secrets.token_urlsafe(32)),
        role=body.role,
        is_active=False,
    )
    db.add(member)
    await db.flush()

    if tenant and tenant.kind == "solo":
        tenant.kind = "firm"

    token = create_purpose_token(
        "invite", member.id, minutes=INVITE_VALID_MINUTES,
        fingerprint=password_fingerprint(member.password_hash),
    )
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="team.invite",
        entity_type="user", entity_id=str(member.id), details={"role": body.role},
    )
    await db.commit()
    await db.refresh(member)
    brand = profile_for(tenant.country if tenant else None).brand_name
    background.add_task(
        _send_invite_email, member.email, user.full_name,
        tenant.name if tenant else brand, token, brand,
    )
    return _member_out(member)


@router.post("/{member_id}/resend-invite")
async def resend_invite(
    member_id: uuid.UUID,
    background: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    require_admin(user)
    member = await db.get(User, member_id)
    if member is None or member.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")
    if member.is_active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Member already active")
    tenant = await db.get(Tenant, user.tenant_id)
    token = create_purpose_token(
        "invite", member.id, minutes=INVITE_VALID_MINUTES,
        fingerprint=password_fingerprint(member.password_hash),
    )
    brand = profile_for(tenant.country if tenant else None).brand_name
    background.add_task(
        _send_invite_email, member.email, user.full_name,
        tenant.name if tenant else brand, token, brand,
    )
    return {"sent": True}


@router.patch("/{member_id}", response_model=TeamMemberOut)
async def update_member(
    member_id: uuid.UUID,
    body: TeamMemberUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    require_admin(user)
    member = await db.get(User, member_id)
    if member is None or member.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")
    if member.id == user.id and body.is_active is False:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot deactivate yourself")
    if body.role is not None:
        if body.role not in ROLES:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid role")
        member.role = body.role
    if body.is_active is not None:
        if body.is_active and not member.is_active:
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
                    status.HTTP_402_PAYMENT_REQUIRED,
                    f"Seat limit reached ({tenant.seats_limit}) — upgrade the plan",
                )
        member.is_active = body.is_active
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="team.update",
        entity_type="user", entity_id=str(member.id),
        details={"role": body.role, "is_active": body.is_active},
    )
    await db.commit()
    await db.refresh(member)
    return _member_out(member)
