"""Team management inside a tenant: lawyers, staff, admins."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models import Tenant, User
from app.schemas.auth import UserOut
from app.security import hash_password
from app.services.audit import log_action

router = APIRouter(prefix="/team", tags=["team"])

ROLES = ("admin", "lawyer", "staff")


def require_manager(user: User) -> None:
    """Admins and lawyers manage the team; staff cannot."""
    if user.role not in ("admin", "lawyer"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")


class TeamMemberIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(min_length=10)
    role: str = "lawyer"


class TeamMemberUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None


class TeamMemberOut(UserOut):
    is_active: bool


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
    return (await db.execute(stmt)).scalars().all()


@router.post("", response_model=TeamMemberOut, status_code=201)
async def add_member(
    body: TeamMemberIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    require_manager(user)
    if body.role not in ROLES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid role")
    existing = (
        await db.execute(select(User).where(User.email == body.email.lower()))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")

    member = User(
        tenant_id=user.tenant_id,
        email=body.email.lower(),
        full_name=body.full_name,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    db.add(member)
    await db.flush()

    tenant = await db.get(Tenant, user.tenant_id)
    if tenant and tenant.kind == "solo":
        tenant.kind = "firm"

    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="team.add",
        entity_type="user", entity_id=str(member.id), details={"role": body.role},
    )
    await db.commit()
    await db.refresh(member)
    return member


@router.patch("/{member_id}", response_model=TeamMemberOut)
async def update_member(
    member_id: uuid.UUID,
    body: TeamMemberUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    require_manager(user)
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
        member.is_active = body.is_active
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="team.update",
        entity_type="user", entity_id=str(member.id),
        details={"role": body.role, "is_active": body.is_active},
    )
    await db.commit()
    await db.refresh(member)
    return member
