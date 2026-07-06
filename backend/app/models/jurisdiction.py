"""Jurisdiction is a first-class entity: deadline rules, templates and the
legal corpus are DATA per jurisdiction, never hard-coded logic."""
import uuid
from datetime import date

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import settings
from app.models.base import Base, TimestampMixin, uuid_pk


class Jurisdiction(Base, TimestampMixin):
    __tablename__ = "jurisdictions"
    __table_args__ = (UniqueConstraint("code"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    code: Mapped[str] = mapped_column(String(8), index=True)  # XK, GB, CN, INTL
    # Localized names: {"sq": "Kosova", "en": "Kosovo", "zh": "科索沃"}
    name: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    deadline_rules: Mapped[list["DeadlineRule"]] = relationship(back_populates="jurisdiction")


class DeadlineRule(Base, TimestampMixin):
    """A procedural deadline rule, e.g. 'appeal within 15 days of judgment
    service' under Kosovo's LPK art. 176. The engine is generic; rules are rows."""

    __tablename__ = "deadline_rules"
    __table_args__ = (UniqueConstraint("jurisdiction_id", "code"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    jurisdiction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jurisdictions.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(64))  # e.g. civil.appeal
    name: Mapped[dict] = mapped_column(JSONB, default=dict)  # localized
    legal_basis: Mapped[str | None] = mapped_column(String(255))  # e.g. "LPK neni 176"
    practice_area: Mapped[str | None] = mapped_column(String(32))  # civil | criminal | ...
    trigger_event: Mapped[str] = mapped_column(String(64))  # e.g. judgment_served
    days: Mapped[int] = mapped_column(Integer)
    day_type: Mapped[str] = mapped_column(String(16), default="calendar")  # calendar | business
    # If the deadline lands on a weekend/holiday, move to next business day
    extend_to_business_day: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text)

    jurisdiction: Mapped[Jurisdiction] = relationship(back_populates="deadline_rules")


class Holiday(Base):
    """Public holidays per jurisdiction, used by business-day math."""

    __tablename__ = "holidays"
    __table_args__ = (UniqueConstraint("jurisdiction_id", "day"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    jurisdiction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jurisdictions.id", ondelete="CASCADE"), index=True
    )
    day: Mapped[date] = mapped_column(Date)
    name: Mapped[dict] = mapped_column(JSONB, default=dict)


class DocumentTemplate(Base, TimestampMixin):
    """Jinja2 template per jurisdiction + language, auto-filled from matter data."""

    __tablename__ = "document_templates"

    id: Mapped[uuid.UUID] = uuid_pk()
    # Global templates have tenant_id NULL; tenants can add their own.
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    jurisdiction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jurisdictions.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(64))  # e.g. civil.lawsuit
    locale: Mapped[str] = mapped_column(String(8), default="sq")
    name: Mapped[dict] = mapped_column(JSONB, default=dict)
    practice_area: Mapped[str | None] = mapped_column(String(32))
    body: Mapped[str] = mapped_column(Text)  # Jinja2 source
    # Declared variables for the UI form: [{"name": "court_name", "label": {...}}]
    variables: Mapped[list] = mapped_column(JSONB, default=list)


class LegalCorpusDoc(Base, TimestampMixin):
    """A law / regulation / precedent indexed for RAG."""

    __tablename__ = "legal_corpus_docs"

    id: Mapped[uuid.UUID] = uuid_pk()
    jurisdiction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jurisdictions.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(500))
    doc_type: Mapped[str] = mapped_column(String(32), default="law")  # law | regulation | case
    reference: Mapped[str | None] = mapped_column(String(255))  # e.g. "Ligji Nr. 03/L-006"
    source_url: Mapped[str | None] = mapped_column(String(1000))
    language: Mapped[str] = mapped_column(String(8), default="sq")

    chunks: Mapped[list["LegalCorpusChunk"]] = relationship(
        back_populates="doc", cascade="all, delete-orphan"
    )


class LegalCorpusChunk(Base):
    __tablename__ = "legal_corpus_chunks"

    id: Mapped[uuid.UUID] = uuid_pk()
    doc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("legal_corpus_docs.id", ondelete="CASCADE"), index=True
    )
    seq: Mapped[int] = mapped_column(Integer)
    section: Mapped[str | None] = mapped_column(String(255))  # e.g. "Neni 176"
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(settings.embedding_dim))

    doc: Mapped[LegalCorpusDoc] = relationship(back_populates="chunks")
