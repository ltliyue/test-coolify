from __future__ import annotations
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.enums import ConsentPurpose, DSARStatus, DSARType, Regulation


class ConsentCreate(BaseModel):
    agency_id: uuid.UUID
    client_id: uuid.UUID | None = None
    subject_email: EmailStr
    purpose: ConsentPurpose
    granted: bool
    do_not_sell: bool = False
    consent_text: str | None = None
    consent_version: str | None = None
    ip_address: str | None = None
    source: str = "api"


class ConsentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subject_hash: str
    purpose: ConsentPurpose
    granted: bool
    do_not_sell: bool
    granted_at: datetime | None
    withdrawn_at: datetime | None


class ConsentWithdraw(BaseModel):
    subject_email: EmailStr
    purpose: ConsentPurpose
    agency_id: uuid.UUID


class DSARCreate(BaseModel):
    agency_id: uuid.UUID
    request_type: DSARType
    regulation: Regulation
    subject_email: EmailStr
    subject_name: str | None = None


class DSARResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agency_id: uuid.UUID
    request_type: DSARType
    regulation: Regulation
    status: DSARStatus
    due_date: datetime | None
    created_at: datetime
    completed_at: datetime | None


class DSARUpdateStatus(BaseModel):
    status: DSARStatus
    notes: str | None = None
    rejection_reason: str | None = None
