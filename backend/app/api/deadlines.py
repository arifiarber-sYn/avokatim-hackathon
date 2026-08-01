import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.matters import get_owned_matter, restricted_visibility_filter
from app.database import get_db
from app.deps import get_current_user
from app.models import Deadline, DeadlineRule, Jurisdiction, Matter, Tenant, User
from app.schemas.matters import (
    DeadlineFromRuleIn,
    DeadlineIn,
    DeadlineOut,
    DeadlineRuleOut,
    JurisdictionOut,
)
from app.services.audit import log_action
from app.services.deadlines import compute_due_date, due_datetime

router = APIRouter(tags=["deadlines"])


@router.get("/jurisdictions", response_model=list[JurisdictionOut])
async def list_jurisdictions(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return (await db.execute(select(Jurisdiction).order_by(Jurisdiction.code))).scalars().all()


@router.get("/jurisdictions/{code}/deadline-rules", response_model=list[DeadlineRuleOut])
async def list_rules(
    code: str,
    practice_area: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    jurisdiction = (
        await db.execute(select(Jurisdiction).where(Jurisdiction.code == code))
    ).scalar_one_or_none()
    if jurisdiction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Jurisdiction not found")
    stmt = select(DeadlineRule).where(DeadlineRule.jurisdiction_id == jurisdiction.id)
    if practice_area:
        stmt = stmt.where(DeadlineRule.practice_area == practice_area)
    return (await db.execute(stmt.order_by(DeadlineRule.code))).scalars().all()


@router.get("/matters/{matter_id}/deadline-rules", response_model=list[DeadlineRuleOut])
async def matter_deadline_rules(
    matter_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rules of the matter's OWN jurisdiction (D-034) — the UI must not
    assume Kosovo now that offices can practice in other countries."""
    matter = await get_owned_matter(db, user, matter_id)
    stmt = (
        select(DeadlineRule)
        .where(DeadlineRule.jurisdiction_id == matter.jurisdiction_id)
        .order_by(DeadlineRule.code)
    )
    return (await db.execute(stmt)).scalars().all()


@router.get("/deadlines/upcoming", response_model=list[DeadlineOut])
async def upcoming_deadlines(
    days: int = 30,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """The lawyer's calendar: everything pending in the next N days."""
    horizon = datetime.now(UTC) + timedelta(days=days)
    stmt = (
        select(Deadline)
        .join(Matter, Matter.id == Deadline.matter_id)
        .where(
            Deadline.tenant_id == user.tenant_id,
            Deadline.status == "pending",
            Deadline.due_at <= horizon,
            restricted_visibility_filter(user),
        )
        .order_by(Deadline.due_at)
    )
    return (await db.execute(stmt)).scalars().all()


@router.get("/matters/{matter_id}/deadlines", response_model=list[DeadlineOut])
async def matter_deadlines(
    matter_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_owned_matter(db, user, matter_id)
    stmt = (
        select(Deadline).where(Deadline.matter_id == matter_id).order_by(Deadline.due_at)
    )
    return (await db.execute(stmt)).scalars().all()


@router.post("/matters/{matter_id}/deadlines", response_model=DeadlineOut, status_code=201)
async def add_manual_deadline(
    matter_id: uuid.UUID,
    body: DeadlineIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_owned_matter(db, user, matter_id)
    deadline = Deadline(tenant_id=user.tenant_id, matter_id=matter_id, **body.model_dump())
    db.add(deadline)
    await db.flush()
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="deadline.create",
        entity_type="deadline", entity_id=str(deadline.id),
    )
    await db.commit()
    await db.refresh(deadline)
    return deadline


@router.post(
    "/matters/{matter_id}/deadlines/from-rule", response_model=DeadlineOut, status_code=201
)
async def add_deadline_from_rule(
    matter_id: uuid.UUID,
    body: DeadlineFromRuleIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """The core value: pick a procedural rule + trigger date, and the engine
    computes the legally correct due date (holidays included)."""
    await get_owned_matter(db, user, matter_id)
    rule = await db.get(DeadlineRule, body.rule_id)
    if rule is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rule not found")

    tenant = await db.get(Tenant, user.tenant_id)
    due = await compute_due_date(
        db, rule, body.trigger_date, region=getattr(tenant, "region", None)
    )
    title = rule.name.get("sq") or rule.code
    deadline = Deadline(
        tenant_id=user.tenant_id,
        matter_id=matter_id,
        kind="deadline",
        title=title,
        due_at=due_datetime(due),
        rule_id=rule.id,
        trigger_date=body.trigger_date,
        legal_basis=rule.legal_basis,
        notes=body.notes,
    )
    db.add(deadline)
    await db.flush()
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="deadline.create_from_rule",
        entity_type="deadline", entity_id=str(deadline.id),
        details={"rule": rule.code, "due": due.isoformat()},
    )
    await db.commit()
    await db.refresh(deadline)
    return deadline


@router.patch("/deadlines/{deadline_id}/status", response_model=DeadlineOut)
async def set_deadline_status(
    deadline_id: uuid.UUID,
    new_status: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if new_status not in ("pending", "done", "missed"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid status")
    deadline = await db.get(Deadline, deadline_id)
    if deadline is None or deadline.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Deadline not found")
    deadline.status = new_status
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="deadline.status",
        entity_type="deadline", entity_id=str(deadline.id), details={"status": new_status},
    )
    await db.commit()
    await db.refresh(deadline)
    return deadline
