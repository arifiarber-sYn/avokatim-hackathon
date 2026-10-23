"""Data-protection models (Law No. 06/L-082 on Protection of Personal Data):
consent records for client communications and processing."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin, uuid_pk

# What the data subject consented to:
#   portal_tos      - accepted ToS/Privacy on first portal login
#   email           - receiving case emails/notifications
#   sms             - receiving SMS reminders
#   ai_processing   - processing of their case data with external AI
CONSENT_KINDS = ["portal_tos", "email", "sms", "ai_processing"]


class ConsentRecord(Base, TenantMixin, TimestampMixin):
    """One consent grant (and its optional revocation) per contact and kind.
    Kept append-only-ish: revoking sets revoked_at; a new grant is a new row,
    so the full history is auditable (Art. 7 - demonstrable consent)."""

    __tablename__ = "consent_records"

    id: Mapped[uuid.UUID] = uuid_pk()
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(32), index=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # How consent was collected: portal | intake | lawyer | import
    method: Mapped[str] = mapped_column(String(32), default="lawyer")
    ip: Mapped[str | None] = mapped_column(String(64))
    notes: Mapped[str | None] = mapped_column(Text)
