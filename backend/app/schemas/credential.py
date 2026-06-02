from __future__ import annotations
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import CredentialStatus, CredentialType


class CredentialCreate(BaseModel):
    agency_id: uuid.UUID
    platform: str
    credential_type: CredentialType
    data: dict
    scopes: list[str] | None = None


class CredentialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agency_id: uuid.UUID
    platform: str
    credential_type: CredentialType
    status: CredentialStatus
    scopes: list[str] | None
    expires_at: datetime | None
    last_refreshed_at: datetime | None


class CredentialUpdate(BaseModel):
    status: CredentialStatus | None = None
    data: dict | None = None
