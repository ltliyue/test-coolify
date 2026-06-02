from __future__ import annotations
from typing import Optional, List
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    message: Optional[str] = None
    category: str
    severity: str
    is_read: bool
    created_at: datetime


class NotificationMarkRead(BaseModel):
    notification_ids: List[str]
