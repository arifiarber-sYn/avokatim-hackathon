import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TenantMixin, TimestampMixin, uuid_pk


class TimeEntry(Base, TenantMixin, TimestampMixin):
    __tablename__ = "time_entries"

    id: Mapped[uuid.UUID] = uuid_pk()
    matter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matters.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    minutes: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)
    billable: Mapped[bool] = mapped_column(Boolean, default=True)
    hourly_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="SET NULL"), index=True
    )


EXPENSE_CATEGORIES = ["court_fee", "bailiff", "expert", "travel", "notary", "translation", "other"]


class Expense(Base, TenantMixin, TimestampMixin):
    """A matter disbursement (court fee, bailiff, expert...) billable to the client."""

    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = uuid_pk()
    matter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matters.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    incurred_on: Mapped[date] = mapped_column(Date)
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(32), default="other")
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    billable: Mapped[bool] = mapped_column(Boolean, default=True)
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="SET NULL"), index=True
    )


TRUST_TRANSACTION_KINDS = ["deposit", "withdrawal"]


class TrustTransaction(Base, TenantMixin, TimestampMixin):
    """Client funds ledger (mjetet e klientit held in trust). Deposits are
    client money received in advance; withdrawals are fees/expenses taken out.
    The ledger can never go negative — enforced at the API layer."""

    __tablename__ = "trust_transactions"

    id: Mapped[uuid.UUID] = uuid_pk()
    matter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matters.id", ondelete="CASCADE"), index=True
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), index=True
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    kind: Mapped[str] = mapped_column(String(16))  # deposit | withdrawal
    occurred_on: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    description: Mapped[str] = mapped_column(Text)
    # Bank statement / receipt reference for reconciliation
    reference: Mapped[str | None] = mapped_column(String(128))
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="SET NULL")
    )


class Invoice(Base, TenantMixin, TimestampMixin):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = uuid_pk()
    number: Mapped[str] = mapped_column(String(64))
    matter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matters.id", ondelete="SET NULL"), index=True
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(16), default="draft", index=True)
    # draft | sent | paid | void
    currency: Mapped[str] = mapped_column(String(8), default="EUR")
    issued_on: Mapped[date | None] = mapped_column(Date)
    due_on: Mapped[date | None] = mapped_column(Date)
    paid_on: Mapped[date | None] = mapped_column(Date)
    # Bank transfer reference / receipt number recorded when marked paid
    payment_reference: Mapped[str | None] = mapped_column(String(128))
    # VAT percentage applied on top of the item subtotal (Kosovo standard: 18)
    vat_rate: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    notes: Mapped[str | None] = mapped_column(Text)
    # Online card payment (Stripe Checkout). Empty when not requested/configured.
    payment_link: Mapped[str | None] = mapped_column(String(1000))
    stripe_session_id: Mapped[str | None] = mapped_column(String(255), index=True)

    items: Mapped[list["InvoiceItem"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )

    @property
    def total(self) -> Decimal:
        return sum((i.amount for i in self.items), Decimal("0"))

    @property
    def vat_amount(self) -> Decimal:
        return (self.total * Decimal(self.vat_rate or 0) / Decimal(100)).quantize(
            Decimal("0.01")
        )

    @property
    def total_with_vat(self) -> Decimal:
        return self.total + self.vat_amount


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id: Mapped[uuid.UUID] = uuid_pk()
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), index=True
    )
    description: Mapped[str] = mapped_column(Text)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("1"))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))

    invoice: Mapped[Invoice] = relationship(back_populates="items")

    @property
    def amount(self) -> Decimal:
        return self.quantity * self.unit_price
