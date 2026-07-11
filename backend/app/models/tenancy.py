import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, uuid_pk


class Tenant(Base, TimestampMixin):
    """A law practice: starts as a solo lawyer, can grow into a firm."""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(20), default="solo")  # solo | firm
    default_locale: Mapped[str] = mapped_column(String(8), default="sq")
    default_jurisdiction_code: Mapped[str] = mapped_column(String(8), default="XK")
    # Opaque token for the public intake form URL; null = form disabled
    intake_token: Mapped[str | None] = mapped_column(String(64), unique=True)

    # Fiscal identity printed on invoices (Kosovo: NUI / VAT no.)
    fiscal_number: Mapped[str | None] = mapped_column(String(32))
    vat_number: Mapped[str | None] = mapped_column(String(32))
    address: Mapped[str | None] = mapped_column(String(500))
    # Bank account details (bank name + IBAN) printed on invoices
    bank_details: Mapped[str | None] = mapped_column(String(500))
    # Default VAT percentage applied to new invoices (Kosovo standard: 18)
    default_vat_rate: Mapped[int] = mapped_column(Integer, default=18, server_default="18")

    # SaaS subscription (platform invoices in app/models/platform_billing.py)
    plan: Mapped[str] = mapped_column(
        String(20), default="trial", server_default="trial"
    )  # trial | solo | firm
    status: Mapped[str] = mapped_column(
        String(20), default="active", server_default="active"
    )  # active | suspended
    seats_limit: Mapped[int] = mapped_column(Integer, default=3, server_default="3")
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Monthly price per active user in EUR. 0 = free forever (founder tenant,
    # strategic partners); overridable per tenant for negotiated deals.
    plan_price_eur: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("24"), server_default="24"
    )
    # Free-form notes for the platform operator (payment references etc.)
    billing_notes: Mapped[str | None] = mapped_column(Text)
    # Firm-wide security policy: force every member to enable TOTP
    require_2fa: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    # Small logo (data URL) shown in the client portal and public intake form
    logo: Mapped[str | None] = mapped_column(Text)

    # --- Data protection (Law 06/L-082) ---
    # When the signup checkbox for ToS/Privacy was ticked
    tos_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Years to keep matter files after closing before flagging for review
    retention_years: Mapped[int] = mapped_column(Integer, default=10, server_default="10")
    # Whether the external AI provider (DeepSeek) may be used; when False the
    # assistant is forced to the local provider (fully compliant route)
    allow_external_ai: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )

    # --- AML (Law 05/L-096) ---
    # Designated compliance officer (obligatory for reporting entities)
    compliance_officer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    # compliance_officer_id adds a second FK path tenants<->users, so the
    # membership relationship must name its FK column explicitly
    users: Mapped[list["User"]] = relationship(
        back_populates="tenant", foreign_keys="User.tenant_id"
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    email: Mapped[str] = mapped_column(String(255), index=True)
    full_name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="lawyer")  # lawyer | staff | admin
    locale: Mapped[str] = mapped_column(String(8), default="sq")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Monthly billable-hours goal, drives the utilization KPI
    billable_hours_target_monthly: Mapped[int] = mapped_column(
        Integer, default=120, server_default="120"
    )

    # TOTP 2FA
    totp_secret: Mapped[str | None] = mapped_column(String(64))
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Platform operator (cross-tenant admin panel); never set via API
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    tenant: Mapped[Tenant] = relationship(back_populates="users", foreign_keys=[tenant_id])
