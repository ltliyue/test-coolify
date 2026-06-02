from __future__ import annotations
from typing import Optional, List, Any
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, model_validator

VALID_FREQUENCIES = {"daily", "weekly", "monthly"}


class ReportScheduleCreate(BaseModel):
    schedule_name: str
    frequency: str  # daily/weekly/monthly
    recipients: List[str]  # email list
    client_id: Optional[uuid.UUID] = None
    metrics_config: Optional[dict] = None
    brand_config_override: Optional[dict] = None

    @model_validator(mode="after")
    def validate_fields(self):
        if self.frequency not in VALID_FREQUENCIES:
            raise ValueError(f"frequency must be one of {VALID_FREQUENCIES}")
        if not self.recipients:
            raise ValueError("recipients must not be empty")
        return self


class ReportScheduleUpdate(BaseModel):
    schedule_name: Optional[str] = None
    frequency: Optional[str] = None
    recipients: Optional[List[str]] = None
    metrics_config: Optional[dict] = None
    brand_config_override: Optional[dict] = None
    is_active: Optional[bool] = None


class ReportScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    agency_id: uuid.UUID
    client_id: Optional[uuid.UUID] = None
    schedule_name: str
    frequency: str
    recipients_count: int = 0  # Return count only — never plaintext emails (compliance)
    metrics_config: Optional[dict] = None
    brand_config_override: Optional[dict] = None
    is_active: bool
    last_sent_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class ReportGenerateRequest(BaseModel):
    client_id: Optional[uuid.UUID] = None
    report_type: str = "campaign_performance"
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class ReportHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    agency_id: uuid.UUID
    schedule_id: Optional[uuid.UUID] = None
    client_id: Optional[uuid.UUID] = None
    report_type: str
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    recipients_count: int = 0
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class ReportDownloadResponse(BaseModel):
    download_url: str
    expires_in_hours: int = 24
