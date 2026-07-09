import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: uuid.UUID
    matter_id: uuid.UUID | None
    family_id: uuid.UUID
    version: int
    is_latest: bool
    filename: str
    mime_type: str
    size_bytes: int
    category: str | None
    ocr_status: str
    has_text: bool = False
    visible_to_client: bool = False
    approval_status: str = "none"
    reviewer_id: uuid.UUID | None = None
    approval_note: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewRequestIn(BaseModel):
    reviewer_id: uuid.UUID


class ReviewDecisionIn(BaseModel):
    decision: str  # "approve" | "request_changes"
    note: str | None = None


class TemplateOut(BaseModel):
    id: uuid.UUID
    code: str
    locale: str
    name: dict
    practice_area: str | None
    variables: list

    model_config = {"from_attributes": True}


class RenderTemplateIn(BaseModel):
    template_id: uuid.UUID
    matter_id: uuid.UUID | None = None
    variables: dict = {}


class RenderToMatterIn(RenderTemplateIn):
    # Edited text from the preview; if omitted the template is re-rendered
    content: str | None = None


class RenderTemplateOut(BaseModel):
    content: str
    filename: str
