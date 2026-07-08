import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class TimeEntryIn(BaseModel):
    matter_id: uuid.UUID
    started_at: datetime
    minutes: int = Field(gt=0)
    description: str
    billable: bool = True
    hourly_rate: Decimal | None = None


class TimeEntryOut(TimeEntryIn):
    id: uuid.UUID
    invoice_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class InvoiceItemIn(BaseModel):
    description: str
    quantity: Decimal = Decimal("1")
    unit_price: Decimal = Decimal("0")


class InvoiceItemOut(InvoiceItemIn):
    id: uuid.UUID
    amount: Decimal

    model_config = {"from_attributes": True}


class InvoiceCreateIn(BaseModel):
    matter_id: uuid.UUID | None = None
    contact_id: uuid.UUID | None = None
    currency: str = "EUR"
    due_on: date | None = None
    notes: str | None = None
    items: list[InvoiceItemIn] = []
    # Pull all unbilled billable time entries of the matter into the invoice
    include_unbilled_time: bool = False
    # None = use the tenant's default VAT rate; 0 = VAT-free invoice
    vat_rate: int | None = Field(None, ge=0, le=30)


class InvoiceOut(BaseModel):
    id: uuid.UUID
    number: str
    matter_id: uuid.UUID | None
    contact_id: uuid.UUID | None
    status: str
    currency: str
    issued_on: date | None
    due_on: date | None
    paid_on: date | None
    payment_reference: str | None
    vat_rate: int = 0
    vat_amount: Decimal = Decimal("0")
    total_with_vat: Decimal = Decimal("0")
    notes: str | None
    items: list[InvoiceItemOut]
    total: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}
