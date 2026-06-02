from __future__ import annotations
"""Notification dispatcher — create notification record + push via WebSocket."""
import uuid
import logging
from typing import Optional, Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification

log = logging.getLogger(__name__)


async def create_notification(
    db: AsyncSession,
    agency_id: uuid.UUID,
    title: str,
    message: Optional[str] = None,
    category: str = "system",
    severity: str = "info",
    user_id: Optional[uuid.UUID] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Notification:
    """create notification recordandattempt WebSocket push。"""
    notif = Notification(
        agency_id=agency_id,
        user_id=user_id,
        title=title,
        message=message,
        category=category,
        severity=severity,
        metadata_=metadata or {},
    )
    db.add(notif)
    await db.flush()
    await db.refresh(notif)

    # attempt WebSocket push
    try:
        from app.services.notifications.manager import ws_manager
        data = {
            "type": "notification",
            "id": str(notif.id),
            "title": title,
            "message": message,
            "category": category,
            "severity": severity,
            "created_at": notif.created_at.isoformat(),
        }
        if user_id:
            await ws_manager.send_to_user(str(user_id), data)
    except Exception as e:
        log.debug("WebSocket push skipped: %s", e)

    return notif
