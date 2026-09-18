import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    matter_id: uuid.UUID | None = None
    conversation_id: uuid.UUID | None = None
    provider: str | None = None  # deepseek | local (default from settings)
    # UI locale — selects the corpus language for citations (official gazette
    # texts exist in sq/sr/tr/bs/en; Albanian is always the fallback)
    locale: str | None = Field(default=None, max_length=8)
    # "ask the matter" (audit 2026-09-18): "full" = context is ALL documents
    # of the matter (budgeted), not the top-k hits of the question
    matter_mode: str | None = Field(default=None, pattern="^(search|full)$")


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    citations: list
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: uuid.UUID
    title: str | None
    matter_id: uuid.UUID | None
    provider: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AskResponse(BaseModel):
    conversation_id: uuid.UUID
    message: MessageOut


class HearingPrepRequest(BaseModel):
    matter_id: uuid.UUID
    extra_instructions: str | None = None
    provider: str | None = None


class SummarizeResponse(BaseModel):
    summary: str
    citations: list
