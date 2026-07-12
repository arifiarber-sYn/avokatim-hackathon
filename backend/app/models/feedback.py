"""Platform feedback: complaints, suggestions and problem reports that any
visitor (no account needed) sends to the platform operator via /kontakti.
Reviewed by superadmins in the /platform panel."""
import uuid

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuid_pk

FEEDBACK_KINDS = ["ankese", "sugjerim", "problem"]
FEEDBACK_STATUSES = ["new", "handled"]


class PlatformFeedback(Base, TimestampMixin):
    __tablename__ = "platform_feedback"

    id: Mapped[uuid.UUID] = uuid_pk()
    kind: Mapped[str] = mapped_column(String(16), default="sugjerim", index=True)
    # Optional — feedback may be anonymous
    name: Mapped[str | None] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="new", index=True)
    handled_note: Mapped[str | None] = mapped_column(String(500))
