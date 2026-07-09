"""Tasks: firm to-dos with assignee, due date and priority, optionally tied
to a matter. Complements deadlines (which are procedural/legal dates)."""
import uuid
from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.matters import get_owned_matter
from app.database import get_db
from app.deps import get_current_user
from app.models import Task, User
from app.models.tasks import TASK_PRIORITIES, TASK_STATUSES
from app.services.audit import log_action

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    matter_id: uuid.UUID | None = None
    assignee_id: uuid.UUID | None = None
    due_date: date | None = None
    priority: str = "normal"


class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    assignee_id: uuid.UUID | None = None
    due_date: date | None = None
    priority: str | None = None
    status: str | None = None


class TaskOut(BaseModel):
    id: uuid.UUID
    matter_id: uuid.UUID | None
    title: str
    description: str | None
    status: str
    priority: str
    due_date: date | None
    assignee_id: uuid.UUID | None
    created_by_id: uuid.UUID | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=list[TaskOut])
async def list_tasks(
    matter_id: uuid.UUID | None = None,
    assignee_id: uuid.UUID | None = None,
    mine: bool = False,
    open_only: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Task).where(Task.tenant_id == user.tenant_id)
    if matter_id:
        await get_owned_matter(db, user, matter_id)
        stmt = stmt.where(Task.matter_id == matter_id)
    if mine:
        stmt = stmt.where(Task.assignee_id == user.id)
    elif assignee_id:
        stmt = stmt.where(Task.assignee_id == assignee_id)
    if open_only:
        stmt = stmt.where(Task.status.in_(["open", "in_progress"]))
    stmt = stmt.order_by(Task.due_date.asc().nulls_last(), Task.created_at.desc()).limit(300)
    return (await db.execute(stmt)).scalars().all()


@router.post("", response_model=TaskOut, status_code=201)
async def create_task(
    body: TaskIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.priority not in TASK_PRIORITIES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid priority")
    if body.matter_id:
        await get_owned_matter(db, user, body.matter_id)
    if body.assignee_id:
        assignee = await db.get(User, body.assignee_id)
        if assignee is None or assignee.tenant_id != user.tenant_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignee not found")
    task = Task(
        tenant_id=user.tenant_id,
        created_by_id=user.id,
        assignee_id=body.assignee_id or user.id,
        **body.model_dump(exclude={"assignee_id"}),
    )
    db.add(task)
    await db.flush()
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="task.create",
        entity_type="task", entity_id=str(task.id), details={"title": body.title},
    )
    await db.commit()
    await db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: uuid.UUID,
    body: TaskUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await db.get(Task, task_id)
    if task is None or task.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    changes = body.model_dump(exclude_unset=True)
    if "status" in changes and changes["status"] not in TASK_STATUSES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid status")
    if "priority" in changes and changes["priority"] not in TASK_PRIORITIES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid priority")
    if changes.get("assignee_id"):
        assignee = await db.get(User, changes["assignee_id"])
        if assignee is None or assignee.tenant_id != user.tenant_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignee not found")
    for k, v in changes.items():
        setattr(task, k, v)
    if changes.get("status") == "done" and task.completed_at is None:
        task.completed_at = datetime.now(UTC)
    elif changes.get("status") in ("open", "in_progress"):
        task.completed_at = None
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="task.update",
        entity_type="task", entity_id=str(task.id), details={"fields": list(changes)},
    )
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await db.get(Task, task_id)
    if task is None or task.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    await db.delete(task)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="task.delete",
        entity_type="task", entity_id=str(task_id),
    )
    await db.commit()
