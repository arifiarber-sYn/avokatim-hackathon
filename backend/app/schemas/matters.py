import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class ContactIn(BaseModel):
    kind: str = "person"
    display_name: str = Field(min_length=1, max_length=255)
    national_id: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    notes: str | None = None
    # Client's communication language (sq/sr/tr/bs/en/zh); null = firm default
    locale: str | None = None


class ContactOut(ContactIn):
    id: uuid.UUID
    portal_enabled: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class MatterPartyIn(BaseModel):
    contact_id: uuid.UUID
    role: str
    notes: str | None = None


class MatterPartyOut(BaseModel):
    id: uuid.UUID
    contact: ContactOut
    role: str
    notes: str | None

    model_config = {"from_attributes": True}


class MatterIn(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    practice_area: str = "civil"
    jurisdiction_code: str = "XK"
    client_id: uuid.UUID | None = None
    court_name: str | None = None
    court_case_number: str | None = None
    opened_on: date | None = None
    extra: dict = {}


class MatterUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    practice_area: str | None = None
    status: str | None = None
    client_id: uuid.UUID | None = None
    responsible_user_id: uuid.UUID | None = None
    court_name: str | None = None
    court_case_number: str | None = None
    opened_on: date | None = None
    closed_on: date | None = None
    extra: dict | None = None


class MatterOut(BaseModel):
    id: uuid.UUID
    reference: str
    title: str
    description: str | None
    practice_area: str
    status: str
    jurisdiction_id: uuid.UUID
    client: ContactOut | None
    responsible_user_id: uuid.UUID
    court_name: str | None
    court_case_number: str | None
    opened_on: date | None
    closed_on: date | None
    restricted: bool = False
    extra: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class MatterMembersUpdate(BaseModel):
    restricted: bool
    user_ids: list[uuid.UUID] = []


class MatterNoteIn(BaseModel):
    body: str = Field(min_length=1)


class MatterNoteOut(BaseModel):
    id: uuid.UUID
    body: str
    author_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class DeadlineIn(BaseModel):
    kind: str = "deadline"
    title: str
    due_at: datetime
    legal_basis: str | None = None
    notes: str | None = None
    remind_days_before: list[int] = [7, 3, 1]


class DeadlineFromRuleIn(BaseModel):
    rule_id: uuid.UUID
    trigger_date: date
    notes: str | None = None


class DeadlineOut(BaseModel):
    id: uuid.UUID
    matter_id: uuid.UUID
    kind: str
    title: str
    due_at: datetime
    legal_basis: str | None
    status: str
    trigger_date: date | None
    notes: str | None

    model_config = {"from_attributes": True}


class IntakeIn(BaseModel):
    client_name: str = Field(min_length=1, max_length=255)
    client_email: str | None = None
    client_phone: str | None = None
    opposing_names: list[str] = []
    summary: str = Field(min_length=1)
    source: str | None = None  # referral | web | phone | walk_in | other


class IntakeOut(BaseModel):
    id: uuid.UUID
    client_name: str
    client_email: str | None
    client_phone: str | None
    opposing_names: list
    summary: str
    source: str | None
    status: str
    conflict_result: dict | None
    ai_classification: dict | None
    matter_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DeadlineRuleOut(BaseModel):
    id: uuid.UUID
    code: str
    name: dict
    legal_basis: str | None
    practice_area: str | None
    trigger_event: str
    days: int
    day_type: str

    model_config = {"from_attributes": True}


class JurisdictionOut(BaseModel):
    id: uuid.UUID
    code: str
    name: dict
    is_active: bool

    model_config = {"from_attributes": True}
