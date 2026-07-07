import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TenantMixin, TimestampMixin, uuid_pk

PRACTICE_AREAS = ["civil", "criminal", "family", "commercial", "labor", "administrative", "other"]
MATTER_STATUSES = ["intake", "open", "on_hold", "closed", "archived"]
PARTY_ROLES = ["client", "opposing_party", "opposing_counsel", "witness", "judge", "expert", "other"]


class Contact(Base, TenantMixin, TimestampMixin):
    """A person or organization: client, opposing party, witness, court..."""

    __tablename__ = "contacts"

    id: Mapped[uuid.UUID] = uuid_pk()
    kind: Mapped[str] = mapped_column(String(16), default="person")  # person | organization
    display_name: Mapped[str] = mapped_column(String(255), index=True)
    national_id: Mapped[str | None] = mapped_column(String(64))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(64))
    address: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)

    # Client portal access (phase 3): set when the lawyer invites the client
    portal_password_hash: Mapped[str | None] = mapped_column(String(255))
    portal_enabled: Mapped[bool] = mapped_column(Boolean, default=False)


class Matter(Base, TenantMixin, TimestampMixin):
    """The case file — the heart of the system."""

    __tablename__ = "matters"
    __table_args__ = (UniqueConstraint("tenant_id", "reference"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    reference: Mapped[str] = mapped_column(String(64))  # e.g. 2026-C-0001
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    practice_area: Mapped[str] = mapped_column(String(32), default="civil")
    status: Mapped[str] = mapped_column(String(16), default="open", index=True)
    jurisdiction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jurisdictions.id"), index=True
    )
    responsible_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )
    client_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id"), index=True
    )
    court_name: Mapped[str | None] = mapped_column(String(255))
    court_case_number: Mapped[str | None] = mapped_column(String(128))
    opened_on: Mapped[date | None] = mapped_column(Date)
    closed_on: Mapped[date | None] = mapped_column(Date)
    # Free-form structured facts the AI can use when drafting (claim value, etc.)
    extra: Mapped[dict] = mapped_column(JSONB, default=dict)

    client: Mapped[Contact | None] = relationship(foreign_keys=[client_id])
    parties: Mapped[list["MatterParty"]] = relationship(
        back_populates="matter", cascade="all, delete-orphan"
    )
    deadlines: Mapped[list["Deadline"]] = relationship(
        back_populates="matter", cascade="all, delete-orphan"
    )


class MatterParty(Base, TimestampMixin):
    __tablename__ = "matter_parties"
    __table_args__ = (UniqueConstraint("matter_id", "contact_id", "role"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    matter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matters.id", ondelete="CASCADE"), index=True
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(32))  # PARTY_ROLES
    notes: Mapped[str | None] = mapped_column(Text)

    matter: Mapped[Matter] = relationship(back_populates="parties")
    contact: Mapped[Contact] = relationship()


class MatterNote(Base, TenantMixin, TimestampMixin):
    __tablename__ = "matter_notes"

    id: Mapped[uuid.UUID] = uuid_pk()
    matter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matters.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)


class Deadline(Base, TenantMixin, TimestampMixin):
    """A deadline, hearing or meeting. Deadlines computed from a DeadlineRule
    keep a reference to the rule and its legal basis."""

    __tablename__ = "deadlines"

    id: Mapped[uuid.UUID] = uuid_pk()
    matter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matters.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(16), default="deadline")  # deadline | hearing | meeting
    title: Mapped[str] = mapped_column(String(500))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deadline_rules.id")
    )
    trigger_date: Mapped[date | None] = mapped_column(Date)
    legal_basis: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending | done | missed
    # Reminder offsets in days before due_at, e.g. [7, 3, 1]
    remind_days_before: Mapped[list] = mapped_column(JSONB, default=lambda: [7, 3, 1])
    notes: Mapped[str | None] = mapped_column(Text)

    matter: Mapped[Matter] = relationship(back_populates="deadlines")


class IntakeRequest(Base, TenantMixin, TimestampMixin):
    """A prospective case: captured, conflict-checked, AI-classified, then
    either converted into a Matter or declined."""

    __tablename__ = "intake_requests"

    id: Mapped[uuid.UUID] = uuid_pk()
    client_name: Mapped[str] = mapped_column(String(255))
    client_email: Mapped[str | None] = mapped_column(String(255))
    client_phone: Mapped[str | None] = mapped_column(String(64))
    opposing_names: Mapped[list] = mapped_column(JSONB, default=list)
    summary: Mapped[str] = mapped_column(Text)
    # Where the client came from: referral | web | phone | walk_in | other
    source: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), default="new", index=True)
    # new | conflict | accepted | declined
    conflict_result: Mapped[dict | None] = mapped_column(JSONB)
    ai_classification: Mapped[dict | None] = mapped_column(JSONB)
    matter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matters.id", ondelete="SET NULL")
    )
