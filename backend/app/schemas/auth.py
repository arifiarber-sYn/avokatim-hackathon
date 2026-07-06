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

    model_config = {"from_attributes": True}
