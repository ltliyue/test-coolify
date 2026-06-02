from __future__ import annotations
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AuthType, IntegrationPlatform, IntegrationStatus, SyncStatus


class ConnectField(BaseModel):
    key: str
    label: str
    required: bool
    secret: bool


class PlatformInfo(BaseModel):
    key: str
    name: str
    description: str
    auth_type: AuthType
    icon: str
    connect_fields: list[ConnectField]


class ConnectRequest(BaseModel):
    platform: IntegrationPlatform
    data: dict


class IntegrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agency_id: uuid.UUID
    platform: IntegrationPlatform
    status: IntegrationStatus
    auth_type: AuthType
    last_sync_at: datetime | None
    connected_at: datetime | None
    config: dict | None
    error_message: str | None


class IntegrationListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    platform: IntegrationPlatform
    status: IntegrationStatus
    last_sync_at: datetime | None
    connected_at: datetime | None


class SyncLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    integration_id: uuid.UUID
    status: SyncStatus
    triggered_by: str | None
    records_fetched: int | None
    records_written: int | None
    started_at: datetime | None
    finished_at: datetime | None
