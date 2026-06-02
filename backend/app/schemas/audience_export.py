from __future__ import annotations
from typing import Optional, Any, List
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict

VALID_EXPORT_PLATFORMS = {"meta_ads", "dv360"}


class AudienceExportRequest(BaseModel):
    platform: str  # meta_ads | dv360
    audience_name: Optional[str] = None


class AudienceExportPreview(BaseModel):
    platform: str
    persona_name: str
    targeting_spec: dict
    warnings: List[str]


class AudienceExportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    agency_id: uuid.UUID
    persona_id: uuid.UUID
    platform: str
    status: str
    external_audience_id: Optional[str] = None
    targeting_spec: Optional[dict] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: datetime
    completed_at: Optional[datetime] = None
