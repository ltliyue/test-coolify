from __future__ import annotations
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    id_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: str
    role_label: str = ""
    role_rank: int = 0
    agency_id: uuid.UUID | None = None
    is_active: bool
    permissions: list[str] = Field(default_factory=list)

    @classmethod
    def from_user(
        cls,
        user,
        permissions: list[str] | None = None,
        role_rank: int = 0,
        role_label: str = "",
    ) -> "UserResponse":
        """M-02/M-03: build the response after decrypting PII fields.

        PR 3: optionally include the user's effective permission codes
        so the frontend can drive page / menu visibility from data.

        PR 5: role_label is the human-readable name resolved from the
        roles table so the UI can show "Agency Admin" instead of
        "agency_admin".
        """
        from app.core.pii_crypto import decrypt_pii
        return cls(
            id=user.id,
            email=decrypt_pii(user.email),
            full_name=decrypt_pii(user.full_name),
            role=str(user.role),
            role_label=role_label or str(user.role),
            role_rank=role_rank,
            agency_id=user.agency_id,
            is_active=user.is_active,
            permissions=sorted(permissions or []),
        )


class RefreshRequest(BaseModel):
    refresh_token: str


class RegisterRequest(BaseModel):
    agency_name: str = Field(min_length=1, max_length=200)
    full_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
