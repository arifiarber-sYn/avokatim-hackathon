import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TenantMixin, TimestampMixin, uuid_pk


class Conversation(Base, TenantMixin, TimestampMixin):
    """A conversation with the Bora AI assistant, optionally tied to a matter."""

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    matter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matters.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str | None] = mapped_column(String(500))
    # Which LLM served this conversation (deepseek | local) — user-selectable
    provider: Mapped[str] = mapped_column(String(32), default="deepseek")

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = uuid_pk()
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(16))  # user | assistant | system
    content: Mapped[str] = mapped_column(Text)
    # RAG citations shown to the lawyer: [{"doc": "...", "section": "Neni 176"}]
    citations: Mapped[list] = mapped_column(JSONB, default=list)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
