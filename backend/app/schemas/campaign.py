from __future__ import annotations
from typing import Optional, Any
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, model_validator


class CampaignMetric(BaseModel):
    date: str
    platform: str
    campaign_id: str
    campaign_name: str
    impressions: int = 0
    clicks: int = 0
    spend: float = 0.0
    reach: int = 0
    conversions: int = 0
    conversion_value: float = 0.0


class CampaignSummary(BaseModel):
    total_spend: float
    total_conversions: int
    total_impressions: int
    total_clicks: int
    platform_breakdown: dict[str, float]
    date_range: dict[str, str]


class BudgetConfigCreate(BaseModel):
    platform: str
    external_campaign_id: str
    campaign_name: Optional[str] = None
    client_id: Optional[uuid.UUID] = None
    daily_budget: Optional[float] = None  # must be >= 0 if provided
    total_budget: Optional[float] = None  # must be >= 0 if provided
    pacing_alert_threshold: float = 0.15
    alert_enabled: bool = True

    @model_validator(mode="after")
    def validate_budgets(self):
        if self.daily_budget is not None and self.daily_budget < 0:
            raise ValueError("daily_budget must be >= 0")
        if self.total_budget is not None and self.total_budget < 0:
            raise ValueError("total_budget must be >= 0")
        return self


class BudgetConfigUpdate(BaseModel):
    campaign_name: Optional[str] = None
    daily_budget: Optional[float] = None  # must be >= 0 if provided
    total_budget: Optional[float] = None  # must be >= 0 if provided
    pacing_alert_threshold: Optional[float] = None
    alert_enabled: Optional[bool] = None


class BudgetConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    agency_id: uuid.UUID
    client_id: Optional[uuid.UUID] = None
    platform: str
    external_campaign_id: str
    campaign_name: Optional[str] = None
    daily_budget: Optional[float] = None
    total_budget: Optional[float] = None
    pacing_alert_threshold: float
    alert_enabled: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class BudgetAlert(BaseModel):
    campaign_name: str
    platform: str
    external_campaign_id: str
    daily_budget: float
    actual_spend: float
    deviation_pct: float
    alert_time: str
