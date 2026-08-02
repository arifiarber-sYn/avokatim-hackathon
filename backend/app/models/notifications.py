"""In-app notification center (D-054). One row per event a user should see
in the bell; email/push/SMS remain separate delivery channels on top."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin, uuid_pk

# Known kinds — used for the per-user "interrupt budget" preferences:
# deadline, suggestion, email, invoice, booking, message, intake,
# briefing, caselaw, agent
NOTIFICATION_KINDS = (
    "deadline",
    "suggestion",
    "email",
    "invoice",
    "booking",
    "message",
    "intake",
    "briefing",
    "caselaw",
    "agent",
)


class Notification(Base, TenantMixin, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = uuid_pk()
    # None = visible to every user of the tenant
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(40), index=True)
    title: Mapped[str] = mapped_column(String(300))
    body: Mapped[str | None] = mapped_column(Text)
    # In-app destination, e.g. /matters/<id>
    url: Mapped[str | None] = mapped_column(String(300))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
