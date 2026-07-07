import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
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

    users: Mapped[list["User"]] = relationship(back_populates="tenant")


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

    tenant: Mapped[Tenant] = relationship(back_populates="users")
