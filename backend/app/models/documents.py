import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import settings
from app.models.base import Base, TenantMixin, TimestampMixin, uuid_pk


class Document(Base, TenantMixin, TimestampMixin):
    """A stored file. New versions are new rows pointing to the same family_id."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = uuid_pk()
    matter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matters.id", ondelete="CASCADE"), index=True
    )
    family_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    filename: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str] = mapped_column(String(128))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    storage_path: Mapped[str] = mapped_column(String(1000))  # relative to documents_dir
    encrypted: Mapped[bool] = mapped_column(Boolean, default=False)

    category: Mapped[str | None] = mapped_column(String(64))  # lawsuit | evidence | judgment...
    # When true, the client sees and can download this document in the portal
    visible_to_client: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    uploaded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    # Extracted text (native PDF text or OCR), used for search and AI analysis
    text_content: Mapped[str | None] = mapped_column(Text)
    # Cached AI summary as JSON {summary, key_points, deadlines} so it is
    # computed once per document version
    ai_summary: Mapped[str | None] = mapped_column(Text)
    ocr_status: Mapped[str] = mapped_column(String(16), default="none")
    # none | pending | done | failed

    # BRAK KI-Leitfaden human oversight (D-044): documents produced from AI
    # output carry this flag; sharing with the client or requesting an
    # e-signature is blocked until a human confirms they reviewed it.
    ai_generated: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    ai_reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    ai_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Internal review workflow: draft goes to a partner before it leaves the firm.
    # none | in_review | approved | changes_requested
    approval_status: Mapped[str] = mapped_column(
        String(20), default="none", server_default="none"
    )
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    approval_note: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(Base):
    """Chunked document text with embeddings for semantic search across a matter."""

    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    seq: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(settings.embedding_dim))

    document: Mapped[Document] = relationship(back_populates="chunks")
