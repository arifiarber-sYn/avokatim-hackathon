import uuid

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """First-run setup: creates the tenant (practice) and its first lawyer."""

    practice_name: str = Field(min_length=2, max_length=200)
    full_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(min_length=10)
    locale: str = "sq"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    requires_2fa: bool = False


class TwoFASetupResponse(BaseModel):
    secret: str
    otpauth_uri: str


class TwoFAVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=8)


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    locale: str
    totp_enabled: bool
    tenant_id: uuid.UUID
    billable_hours_target_monthly: int
    is_superadmin: bool = False
    email_verified: bool = False
    # Tenant subscription summary (drives the trial banner in the UI)
    tenant_plan: str | None = None
    tenant_status: str | None = None
    tenant_trial_ends_at: str | None = None
    tenant_require_2fa: bool = False
    # Drives profession-conditional UI (notary offices see no marketplace)
    tenant_profession: str = "lawyer"

    model_config = {"from_attributes": True}


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=200)
    billable_hours_target_monthly: int | None = Field(default=None, ge=1, le=744)


class SignupRequest(BaseModel):
    """Public self-service signup: creates a new tenant on a 30-day trial."""

    practice_name: str = Field(min_length=2, max_length=200)
    full_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(min_length=10)
    locale: str = "sq"
    # Which legal profession the office practices: lawyer (default) or notary
    profession: str = Field(default="lawyer", pattern="^(lawyer|notary)$")
    # ToS/Privacy checkbox (Law 06/L-082) — must be true
    accept_tos: bool = False
    # Lawyer-brings-lawyer program: the referrer's share code (?ref=)
    referral_code: str | None = Field(default=None, max_length=16)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=10)


class VerifyEmailRequest(BaseModel):
    token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=10)


class AcceptInviteRequest(BaseModel):
    token: str
    password: str = Field(min_length=10)
