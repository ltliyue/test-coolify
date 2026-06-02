from __future__ import annotations
from typing import Optional, Any, Dict, List
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PersonaCreate(BaseModel):
    name: str
    description: Optional[str] = None
    psychographics: Optional[Dict[str, Any]] = None
    channel_preferences: Optional[Dict[str, Any]] = None
    recommended_tone: Optional[str] = None
    client_id: Optional[str] = None


class PersonaUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    psychographics: Optional[Dict[str, Any]] = None
    channel_preferences: Optional[Dict[str, Any]] = None
    recommended_tone: Optional[str] = None


class PersonaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    agency_id: Optional[uuid.UUID] = None
    name: str
    description: Optional[str] = None
    psychographics: Optional[Dict[str, Any]] = None
    channel_preferences: Optional[Dict[str, Any]] = None
    recommended_tone: Optional[str] = None
    source: Optional[str] = None
    model_used: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class PersonaGenerateRequest(BaseModel):
    """Request payload for AI-driven persona generation."""
    prompt: str = "Generate 3 detailed marketing personas for this brand"
    client_id: Optional[str] = None
    count: int = 3
