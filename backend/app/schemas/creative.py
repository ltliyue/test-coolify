from __future__ import annotations
from typing import Optional, List
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class GenerationCreate(BaseModel):
    prompt: str
    platforms: List[str] = ["INSTAGRAM", "FACEBOOK", "TIKTOK", "TWITTER"]
    client_id: Optional[str] = None


class GenerationResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    platform: str
    copy_text: Optional[str] = None
    image_url: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime


class GenerationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    agency_id: Optional[uuid.UUID] = None
    status: str
    prompt: str
    error_message: Optional[str] = None
    agent_type: Optional[str] = None
    results: List[GenerationResultResponse] = []
    created_at: datetime
    updated_at: datetime
