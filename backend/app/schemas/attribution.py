from __future__ import annotations
from typing import Optional, Any, Dict, List
import uuid
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict


class AttributionReportCreate(BaseModel):
    title: str = "Attribution Report"
    prompt: str = "Generate a multi-touch attribution report for all channels"
    report_type: str = "multi_touch"
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None
    client_id: Optional[str] = None


class AttributionReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    agency_id: uuid.UUID
    title: str
    report_type: str
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None
    channels: Optional[Any] = None
    results: Optional[Dict[str, Any]] = None
    insights: Optional[str] = None
    model_used: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
