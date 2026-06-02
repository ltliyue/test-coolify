from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AgencyCreate(BaseModel):
    name: str
    plan: str = "starter"
    monthly_token_budget: int = 1000000


class AgencyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    status: str
    plan: str
    brand_config: dict[str, Any] | None
    monthly_token_budget: int
    created_at: datetime


class ClientCreate(BaseModel):
    name: str
    agency_id: uuid.UUID
    verticals: list[str] = []
    brand_config: dict[str, Any] | None = None


class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agency_id: uuid.UUID
    name: str
    slug: str
    status: str
    verticals: list[str]
    brand_config: dict[str, Any] | None
    created_at: datetime
