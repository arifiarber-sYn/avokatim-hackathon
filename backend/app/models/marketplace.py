"""Public marketplace: citizens (platform-level, no tenant) meet lawyers.

A citizen posts a CaseRequest; a lawyer claims it, which runs the existing
conflict check and creates an IntakeRequest (source="marketplace"). When the
intake is accepted, the citizen becomes a Contact with portal access using
the same credentials.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuid_pk

CASE_REQUEST_STATUSES = ["open", "claimed", "converted", "closed"]
CASE_URGENCIES = ["normal", "urgent", "sos"]
# Bar-license verification lifecycle: none (no license entered) -> pending
# (entered, awaiting operator check against the public OAK registry) ->
# verified | rejected (with a note; editing the license resubmits).
VERIFICATION_STATUSES = ["none", "pending", "verified", "rejected"]


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
    # OAK (Kosovo Bar Association) license verification — the directory's
    # trust gate: only verified lawyers are listed publicly or may claim
    # marketplace cases. Verification is manual (superadmin checks the
    # public OAK registry) because OAK has no lookup API.
    oak_license_no: Mapped[str | None] = mapped_column(String(64))
    verification_status: Mapped[str] = mapped_column(
        String(16), default="none", server_default="none", index=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verification_note: Mapped[str | None] = mapped_column(String(255))
    # Transparent pricing (optional): consultation fee shown in the directory
    consult_fee_eur: Mapped[int | None] = mapped_column(Integer)
    # Consultation booking (Phase 4): weekly recurring availability windows,
    # e.g. [{"day": 0, "start": "09:00", "end": "12:00"}] (0 = Monday).
    booking_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    booking_slots: Mapped[list] = mapped_column(JSONB, default=list)


BOOKING_STATUSES = ["pending", "confirmed", "declined", "cancelled"]


class ConsultBooking(Base, TimestampMixin):
    """A citizen's consultation reservation with a directory lawyer.

    Created pending; the lawyer confirms or declines. Slots come from the
    lawyer's weekly availability minus existing pending/confirmed bookings.
    """

    __tablename__ = "consult_bookings"

    id: Mapped[uuid.UUID] = uuid_pk()
    citizen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citizen_users.id", ondelete="CASCADE"), index=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    lawyer_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    duration_min: Mapped[int] = mapped_column(Integer, default=30)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    note: Mapped[str | None] = mapped_column(Text)


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


class CaseReview(Base, TimestampMixin):
    """Post-engagement review by the citizen who owned the case.

    Only the citizen whose claimed case reached converted/closed may review,
    exactly once. Prompts rate the service experience (communication, speed,
    clarity) — never the legal outcome, which would create regulatory risk
    for both the platform and the lawyer.
    """

    __tablename__ = "case_reviews"
    __table_args__ = (UniqueConstraint("case_request_id"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    case_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("case_requests.id", ondelete="CASCADE"), index=True
    )
    citizen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citizen_users.id", ondelete="CASCADE"), index=True
    )
    # The firm that handled the case (solo lawyer == their tenant)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    rating_communication: Mapped[int] = mapped_column(Integer)  # 1..5
    rating_speed: Mapped[int] = mapped_column(Integer)  # 1..5
    rating_clarity: Mapped[int] = mapped_column(Integer)  # 1..5
    comment: Mapped[str | None] = mapped_column(Text)


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
