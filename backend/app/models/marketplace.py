"""Public marketplace: citizens (platform-level, no tenant) meet lawyers.

A citizen posts a CaseRequest; a lawyer claims it, which runs the existing
conflict check and creates an IntakeRequest (source="marketplace"). When the
intake is accepted, the citizen becomes a Contact with portal access using
the same credentials.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuid_pk

CASE_REQUEST_STATUSES = ["open", "claimed", "converted", "closed"]
CASE_URGENCIES = ["normal", "urgent", "sos"]


class CitizenUser(Base, TimestampMixin):
    """A member of the public — NOT a tenant user and NOT a contact.

    Lives at platform level; becomes a tenant Contact only when a lawyer
    accepts their case.
    """

    __tablename__ = "citizen_users"
    __table_args__ = (UniqueConstraint("email"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(64))
    full_name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(255))
    locale: Mapped[str] = mapped_column(String(8), default="sq")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Privacy-policy acceptance at signup (Law 06/L-082, demonstrable consent)
    privacy_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LawyerProfile(Base, TimestampMixin):
    """Opt-in public directory entry for a tenant user (lawyer)."""

    __tablename__ = "lawyer_profiles"
    __table_args__ = (UniqueConstraint("user_id"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    is_visible: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    # SOS duty roster (Phase 3): opted-in lawyers get instant alerts for
    # urgent citizen requests
    sos_on_duty: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    bio: Mapped[str | None] = mapped_column(Text)
    practice_areas: Mapped[list] = mapped_column(JSONB, default=list)  # PRACTICE_AREAS codes
    cities: Mapped[list] = mapped_column(JSONB, default=list)
    languages: Mapped[list] = mapped_column(JSONB, default=list)  # locale codes
    # Small photo as data URL (same convention as Tenant.logo)
    photo: Mapped[str | None] = mapped_column(Text)


class CaseRequest(Base, TimestampMixin):
    """A citizen's request for legal help, visible to lawyers until claimed."""

    __tablename__ = "case_requests"

    id: Mapped[uuid.UUID] = uuid_pk()
    citizen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citizen_users.id", ondelete="CASCADE"), index=True
    )
    category: Mapped[str] = mapped_column(String(32), default="other")  # PRACTICE_AREAS
    description: Mapped[str] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(120))
    locale: Mapped[str] = mapped_column(String(8), default="sq")
    urgency: Mapped[str] = mapped_column(String(16), default="normal")
    status: Mapped[str] = mapped_column(String(16), default="open", index=True)
    # Directed request: only this tenant sees it (from the directory's
    # "contact this lawyer" button). Null = open to every lawyer.
    directed_tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL")
    )
    claimed_by_tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"), index=True
    )
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    intake_request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("intake_requests.id", ondelete="SET NULL")
    )
    # Set when the intake is accepted and the citizen becomes a portal client
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL")
    )
    closed_reason: Mapped[str | None] = mapped_column(String(255))


class CaseRequestMessage(Base, TimestampMixin):
    """Simple citizen <-> claiming-lawyer thread before the formal intake
    acceptance (afterwards communication moves to the matter portal)."""

    __tablename__ = "case_request_messages"

    id: Mapped[uuid.UUID] = uuid_pk()
    case_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("case_requests.id", ondelete="CASCADE"), index=True
    )
    sender: Mapped[str] = mapped_column(String(16))  # citizen | lawyer
    sender_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    body: Mapped[str] = mapped_column(Text)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
