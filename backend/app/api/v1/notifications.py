from __future__ import annotations
"""F-17 notification REST API — list, unread count, mark as read."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_db import get_tenant_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse, NotificationMarkRead

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(False),
    category: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    """Get the notification list for the current user (including agency broadcasts)."""
    stmt = select(Notification).where(
        Notification.agency_id == user.agency_id,
        (Notification.user_id == user.id) | (Notification.user_id.is_(None)),
    )
    if unread_only:
        stmt = stmt.where(Notification.is_read == False)  # noqa: E712
    if category:
        stmt = stmt.where(Notification.category == category)
    stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)

    result = await db.execute(stmt)
    return [NotificationResponse.model_validate(n) for n in result.scalars().all()]


@router.get("/unread-count")
async def unread_count(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    """Get the unread notification count."""
    count = (await db.execute(
        select(func.count(Notification.id)).where(
            Notification.agency_id == user.agency_id,
            (Notification.user_id == user.id) | (Notification.user_id.is_(None)),
            Notification.is_read == False,  # noqa: E712
        )
    )).scalar() or 0
    return {"unread_count": count}


@router.post("/mark-read", status_code=status.HTTP_200_OK)
async def mark_notifications_read(
    body: NotificationMarkRead,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    """Mark the specified notifications as read."""
    ids = [uuid.UUID(nid) for nid in body.notification_ids]
    await db.execute(
        update(Notification)
        .where(
            Notification.id.in_(ids),
            Notification.agency_id == user.agency_id,
        )
        .values(is_read=True)
    )
    await db.commit()
    return {"marked": len(ids)}


@router.post("/mark-all-read", status_code=status.HTTP_200_OK)
async def mark_all_read(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    """convertall notificationmarkto read。"""
    result = await db.execute(
        update(Notification)
        .where(
            Notification.agency_id == user.agency_id,
            (Notification.user_id == user.id) | (Notification.user_id.is_(None)),
            Notification.is_read == False,  # noqa: E712
        )
        .values(is_read=True)
    )
    await db.commit()
    return {"marked": result.rowcount}
