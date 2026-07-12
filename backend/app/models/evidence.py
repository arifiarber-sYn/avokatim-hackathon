"""Evidence vault: citizen recordings with probative value (D-018).

Modeled on ACLU Mobile Justice: audio/video is uploaded in small chunks
WHILE recording, so the evidence survives even if the phone is seized or
destroyed. Each chunk is hashed (SHA-256) and chained to the previous one;
the server timestamps every chunk on arrival — together this gives a
verifiable chain of custody (content + order + time), which is what courts
ask about first.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuid_pk

EVIDENCE_KINDS = ["sos_audio", "sos_video", "call"]
EVIDENCE_STATUSES = ["recording", "finished"]


class EvidenceSession(Base, TimestampMixin):
    __tablename__ = "evidence_sessions"

    id: Mapped[uuid.UUID] = uuid_pk()
    citizen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citizen_users.id", ondelete="CASCADE"), index=True
    )
    # Attached to the SOS case so the claiming lawyer arrives prepared
    case_request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("case_requests.id", ondelete="SET NULL"), index=True
    )
    kind: Mapped[str] = mapped_column(String(16), default="sos_audio")
    mime: Mapped[str] = mapped_column(String(64), default="audio/webm")
    status: Mapped[str] = mapped_column(String(16), default="recording")
    locale: Mapped[str] = mapped_column(String(8), default="sq")
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    total_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    # Rolling chain hash: H_n = sha256(H_{n-1} || sha256(chunk_n)); the final
    # value fingerprints the entire recording AND its order.
    chain_hash: Mapped[str | None] = mapped_column(String(64))
    # Whisper transcript, filled in the background after finish
    transcript: Mapped[str | None] = mapped_column(Text)
    transcript_status: Mapped[str] = mapped_column(String(16), default="none")
    # Consent bookkeeping (Law 06/L-082: demonstrable consent)
    consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EvidenceChunk(Base, TimestampMixin):
    __tablename__ = "evidence_chunks"
    __table_args__ = (UniqueConstraint("session_id", "seq"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evidence_sessions.id", ondelete="CASCADE"),
        index=True,
    )
    seq: Mapped[int] = mapped_column(Integer)
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    prev_hash: Mapped[str | None] = mapped_column(String(64))
    chain_hash: Mapped[str] = mapped_column(String(64))
    # created_at (TimestampMixin) is the server-side arrival timestamp
