"""Platform subscription billing: the operator invoices tenants (law
practices) for their monthly SaaS subscription.

Revenue model (D-016): citizens never pay the platform; lawyers pay a flat
per-seat monthly subscription which includes unlimited marketplace leads.
The platform NEVER takes a percentage of lawyer fees (Avvo Legal Services
was shut down over exactly that — impermissible fee splitting).
"""
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuid_pk

PLATFORM_INVOICE_STATUSES = ["open", "paid", "void"]


class PlatformInvoice(Base, TimestampMixin):
    """One tenant's subscription invoice for one calendar month.

    Generated idempotently (unique per tenant+period) by the billing loop
    or on demand from the platform panel. Paid by bank transfer (marked by
    the operator) or by card via Stripe Checkout when configured.
    """

    __tablename__ = "platform_invoices"
    __table_args__ = (UniqueConstraint("tenant_id", "period_start"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    number: Mapped[str] = mapped_column(String(64))  # P-YYYY-NNNN
    # Billing period (calendar month)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    plan: Mapped[str] = mapped_column(String(20))  # solo | firm (snapshot)
    seats: Mapped[int] = mapped_column(Integer, default=1)
    unit_price_eur: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    amount_eur: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(16), default="open", index=True)
    issued_on: Mapped[date] = mapped_column(Date)
    due_on: Mapped[date] = mapped_column(Date)
    paid_on: Mapped[date | None] = mapped_column(Date)
    # Bank transfer reference or "Stripe <intent>" recorded on payment
    payment_reference: Mapped[str | None] = mapped_column(String(128))
    # Online card payment (Stripe Checkout), when configured
    payment_link: Mapped[str | None] = mapped_column(String(1000))
    stripe_session_id: Mapped[str | None] = mapped_column(String(255), index=True)
    notes: Mapped[str | None] = mapped_column(Text)
