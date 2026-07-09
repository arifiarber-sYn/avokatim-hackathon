"""AML models (Law No. 05/L-096 on Prevention of Money Laundering and
Combating Terrorist Financing). Lawyers are reporting entities for real
estate, funds management (trust ledger) and company formation work."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin, uuid_pk


class SuspicionReport(Base, TenantMixin, TimestampMixin):
    """Internal suspicious-activity report: prepared by the lawyer or the
    compliance officer, exported as PDF for submission to the FIU-Kosovo
    (NjIF-K). The platform never sends anything automatically."""

    __tablename__ = "suspicion_reports"

    id: Mapped[uuid.UUID] = uuid_pk()
    matter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matters.id", ondelete="SET NULL"), index=True
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), index=True
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    # Matched NjIF-K indicator codes (from the seeded indicator list)
    indicators: Mapped[list] = mapped_column(JSONB, default=list)
    description: Mapped[str] = mapped_column(Text)
    # draft | submitted (marked manually after filing with NjIF-K)
    status: Mapped[str] = mapped_column(String(16), default="draft")
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
