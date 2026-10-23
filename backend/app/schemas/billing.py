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


class ExpenseIn(BaseModel):
    matter_id: uuid.UUID
    incurred_on: date
    description: str
    category: str = "other"
    amount: Decimal = Field(gt=0)
    billable: bool = True


class ExpenseOut(ExpenseIn):
    id: uuid.UUID
    invoice_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TrustTransactionIn(BaseModel):
    matter_id: uuid.UUID
    kind: str = Field(pattern="^(deposit|withdrawal)$")
    occurred_on: date
    amount: Decimal = Field(gt=0)
    description: str
    reference: str | None = None
    # AML (Law 05/L-096): declared source of funds for deposits
    source_of_funds: str | None = None


class TrustTransactionOut(TrustTransactionIn):
    id: uuid.UUID
    contact_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TrustBalanceOut(BaseModel):
    matter_id: uuid.UUID
    matter_reference: str
    matter_title: str
    client_name: str | None
    balance: Decimal


class FeeTariffItemOut(BaseModel):
    id: uuid.UUID
    code: str
    tariff_no: str | None
    name: dict
    practice_area: str | None
    amount: Decimal
    unit: str | None
    legal_basis: str | None
    notes: str | None

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
    # Pull all unbilled billable expenses of the matter into the invoice
    include_unbilled_expenses: bool = False
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
    payment_link: str | None = None
    vat_rate: int = 0
    vat_amount: Decimal = Decimal("0")
    total_with_vat: Decimal = Decimal("0")
    mahnung_level: int = 0
    last_mahnung_at: datetime | None = None
    notes: str | None
    items: list[InvoiceItemOut]
    total: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}
