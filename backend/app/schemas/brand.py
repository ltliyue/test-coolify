from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, ConfigDict


class BrandConfigUpdate(BaseModel):
    """Brand-config update payload (all fields optional, PATCH semantics)."""
    name: Optional[str] = None                # Brand name, e.g. "Acme Corp"
    logo_url: Optional[str] = None            # Public logo URL
    primary_color: Optional[str] = None       # Primary brand color, e.g. "#FF6B35"
    secondary_color: Optional[str] = None
    brand_voice: Optional[str] = None         # Brand-voice description, consumed by AI
    industry: Optional[str] = None            # Industry, e.g. "e-commerce"
    target_audience: Optional[str] = None     # Target-audience description
    website_url: Optional[str] = None
    tagline: Optional[str] = None


class BrandConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    agency_id: str
    name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    brand_voice: Optional[str] = None
    industry: Optional[str] = None
    target_audience: Optional[str] = None
    website_url: Optional[str] = None
    tagline: Optional[str] = None
