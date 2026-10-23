import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin, uuid_pk

TASK_STATUSES = ["open", "in_progress", "done", "cancelled"]
TASK_PRIORITIES = ["low", "normal", "high", "urgent"]


class Task(Base, TenantMixin, TimestampMixin):
    """A to-do item, optionally tied to a matter, assigned to a team member."""

    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = uuid_pk()
    matter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matters.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="open", index=True)
    priority: Mapped[str] = mapped_column(String(16), default="normal")
    due_date: Mapped[date | None] = mapped_column(Date, index=True)
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
