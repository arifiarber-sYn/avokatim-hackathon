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
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, uuid_pk


class Tenant(Base, TimestampMixin):
    """A legal office: a law practice or a notary office. Starts solo,
    can grow into a firm."""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(20), default="solo")  # solo | firm
    # Which legal profession this office practices. Notary offices get the
    # same digital office + AI but no case marketplace (notaries are impartial
    # public officers with fixed tariffs — competing for cases is off-limits).
    profession: Mapped[str] = mapped_column(
        String(20), default="lawyer", server_default="lawyer"
    )  # lawyer | notary
    default_locale: Mapped[str] = mapped_column(String(8), default="sq")
    default_jurisdiction_code: Mapped[str] = mapped_column(String(8), default="XK")
    # Country the office operates in (D-034): scopes the directory,
    # marketplace and public stats; see app/jurisdictions.py for the profile
    country: Mapped[str] = mapped_column(String(8), default="XK", server_default="XK", index=True)
    # Internal/test account (audit 2026-09-18): excluded from growth stats
    # and lifecycle emails; set by the platform admin, never by signup.
    is_test: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    # Sub-national unit the office sits in (DE: Bundesland code NW/BY/…) —
    # selects the regional holiday calendar for deadline math; NULL = none
    region: Mapped[str | None] = mapped_column(String(8))
    # Opaque token for the public intake form URL; null = form disabled
    intake_token: Mapped[str | None] = mapped_column(String(64), unique=True)
    # Office "memory" for Ava (Vincent-Skills-lite): free-text preferences the
    # lawyer sets once — drafting style, citation habits, standard clauses —
    # appended to the assistant's system prompt on every office request.
    assistant_style: Mapped[str | None] = mapped_column(Text)

    # Fiscal identity printed on invoices (Kosovo: NUI / VAT no.)
    fiscal_number: Mapped[str | None] = mapped_column(String(32))
    vat_number: Mapped[str | None] = mapped_column(String(32))
    address: Mapped[str | None] = mapped_column(String(500))
    # Bank account details (bank name + IBAN) printed on invoices
    bank_details: Mapped[str | None] = mapped_column(String(500))
    # Structured IBAN for e-invoices (ZUGFeRD/XRechnung SEPA payment means);
    # bank_details above stays the free-text line printed on the PDF
    iban: Mapped[str | None] = mapped_column(String(34))
    # Default VAT percentage applied to new invoices (Kosovo standard: 18)
    default_vat_rate: Mapped[int] = mapped_column(Integer, default=18, server_default="18")

    # DATEV export configuration (DE offices, D-037): consultant/client number
    # of the office's Steuerberater and the SKR03 accounts used in the EXTF
    # Buchungsstapel. NULL = code defaults (8400 revenue, 10000 debtor).
    datev_consultant_no: Mapped[str | None] = mapped_column(String(7))
    datev_client_no: Mapped[str | None] = mapped_column(String(5))
    datev_revenue_account: Mapped[str | None] = mapped_column(String(9))
    datev_debtor_account: Mapped[str | None] = mapped_column(String(9))

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
    # Referral program: this tenant's own share code, and the code that
    # brought them here (recorded at signup for the lawyer-brings-lawyer program)
    referral_code: Mapped[str | None] = mapped_column(String(16), unique=True)
    referred_by_code: Mapped[str | None] = mapped_column(String(16))
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
    # Fernet-encrypted with an enc:v1: prefix (D-033) — needs room
    totp_secret: Mapped[str | None] = mapped_column(String(255))
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Bumped to instantly invalidate every issued JWT for this user (D-033):
    # tokens carry the version at issue time and deps.py compares on each
    # request. Incremented on password reset/change.
    token_version: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Platform operator (cross-tenant admin panel); never set via API
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # One-shot onboarding nudge: set when the "activate your public profile"
    # reminder email has been sent (48h after signup, only if still inactive)
    profile_nudge_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Interrupt budget (D-054): per-kind delivery mode for notifications,
    # e.g. {"invoice": "center"} — "push" (default) also sends Web Push,
    # "center" only lands in the in-app bell.
    notification_prefs: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )

    tenant: Mapped[Tenant] = relationship(back_populates="users", foreign_keys=[tenant_id])


class ApiToken(Base, TimestampMixin):
    """Personal access token for external integrations (public API).

    The plaintext token (`avk_<40 hex>`) is shown ONCE at creation and only
    its SHA-256 is stored. It authenticates as the creating user (same
    permissions, same tenant RLS scoping in deps.py); `scope="read"` tokens
    are rejected on any non-GET request.
    """

    __tablename__ = "api_tokens"

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    # sha256 hex of the full plaintext token — unique lookup key
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    # first characters of the plaintext ("avk_ab12cd34…") for identification
    prefix: Mapped[str] = mapped_column(String(16))
    scope: Mapped[str] = mapped_column(String(16), default="read")  # read | read_write
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship()
