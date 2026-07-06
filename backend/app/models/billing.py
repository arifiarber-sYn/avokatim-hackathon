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
    notes: Mapped[str | None] = mapped_column(Text)

    items: Mapped[list["InvoiceItem"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )

    @property
    def total(self) -> Decimal:
        return sum((i.amount for i in self.items), Decimal("0"))


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
