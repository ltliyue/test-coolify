"""
F-17：notificationsystemtest。
Covers: notification creation (dispatcher), REST API (list / unread count / mark read), authentication checks.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool


# Helper：directlyuse dispatcher create notification
async def _create_test_notification(agency_id, user_id, title="Test Notification", category="system"):
    """via dispatcher create notification。"""
    from app.services.notifications.dispatcher import create_notification

    engine = create_async_engine(
        "postgresql+asyncpg://receptiviq:receptiviq@localhost:5432/receptiviq",
        poolclass=NullPool,
    )
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as db:
        notif = await create_notification(
            db=db,
            agency_id=agency_id,
            user_id=user_id,
            title=title,
            message=f"Message for {title}",
            category=category,
            severity="info",
        )
        await db.commit()
    await engine.dispose()
    return notif


# ── TC-NTF-01：notification listto empty ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_list_notifications_empty(client: AsyncClient, auth_headers: dict):
    """A new Agency's notification list should be empty."""
    resp = await client.get("/api/v1/notifications", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


# ── TC-NTF-02: after creation the notification is queryable ─────────────────────
@pytest.mark.asyncio
async def test_create_and_list_notification(
    client: AsyncClient, auth_headers: dict, test_agency, test_user
):
    """After creating a notification via the dispatcher, the list should return that item."""
    await _create_test_notification(test_agency.id, test_user.id, "Hello World")

    resp = await client.get("/api/v1/notifications", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 1
    assert items[0]["title"] == "Hello World"
    assert items[0]["is_read"] is False


# ── TC-NTF-03: unread count ─────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_unread_count(
    client: AsyncClient, auth_headers: dict, test_agency, test_user
):
    """After creating 2 notifications the unread count should be 2."""
    await _create_test_notification(test_agency.id, test_user.id, "Notif 1")
    await _create_test_notification(test_agency.id, test_user.id, "Notif 2")

    resp = await client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["unread_count"] == 2


# ── TC-NTF-04：mark singleread ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_mark_notification_read(
    client: AsyncClient, auth_headers: dict, test_agency, test_user
):
    """After marking a single notification read, the unread count decreases."""
    notif = await _create_test_notification(test_agency.id, test_user.id, "To Mark")

    # markread
    resp = await client.post(
        "/api/v1/notifications/mark-read",
        json={"notification_ids": [str(notif.id)]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["marked"] == 1

    # Verify the unread count
    count_resp = await client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert count_resp.json()["unread_count"] == 0


# ── TC-NTF-05：mark allread ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_mark_all_read(
    client: AsyncClient, auth_headers: dict, test_agency, test_user
):
    """mark-all-read should convertall notificationmarkto read。"""
    await _create_test_notification(test_agency.id, test_user.id, "A1")
    await _create_test_notification(test_agency.id, test_user.id, "A2")
    await _create_test_notification(test_agency.id, test_user.id, "A3")

    resp = await client.post("/api/v1/notifications/mark-all-read", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["marked"] == 3

    count_resp = await client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert count_resp.json()["unread_count"] == 0


# ── TC-NTF-06: filter by category ───────────────────────────────────────────────
@pytest.mark.asyncio
async def test_filter_by_category(
    client: AsyncClient, auth_headers: dict, test_agency, test_user
):
    """?category=ai_task should return only ai_task-category notifications."""
    await _create_test_notification(test_agency.id, test_user.id, "AI Done", category="ai_task")
    await _create_test_notification(test_agency.id, test_user.id, "System Msg", category="system")

    resp = await client.get(
        "/api/v1/notifications?category=ai_task", headers=auth_headers
    )
    assert resp.status_code == 200
    items = resp.json()
    assert all(n["category"] == "ai_task" for n in items)


# ── TC-NTF-07：unread_only filter ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_unread_only_filter(
    client: AsyncClient, auth_headers: dict, test_agency, test_user
):
    """After marking one as read, unread_only=true should not return read notifications."""
    n1 = await _create_test_notification(test_agency.id, test_user.id, "Read Me")
    await _create_test_notification(test_agency.id, test_user.id, "Still Unread")

    # mark n1 read
    await client.post(
        "/api/v1/notifications/mark-read",
        json={"notification_ids": [str(n1.id)]},
        headers=auth_headers,
    )

    resp = await client.get(
        "/api/v1/notifications?unread_only=true", headers=auth_headers
    )
    assert resp.status_code == 200
    items = resp.json()
    assert all(n["is_read"] is False for n in items)
    assert len(items) == 1


# ── TC-NTF-08: WebSocket manager unit test ──────────────────────────────────────
def test_ws_manager_initial_state():
    """ConnectionManager initial stateshould to  0 connection。"""
    from app.services.notifications.manager import ConnectionManager
    mgr = ConnectionManager()
    assert mgr.active_connections_count == 0


# ── TC-NTF-09：authenticationcheck ──────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_notifications_requires_auth(client: AsyncClient):
    """/notifications without JWT should return 401。"""
    resp = await client.get("/api/v1/notifications")
    assert resp.status_code == 401
