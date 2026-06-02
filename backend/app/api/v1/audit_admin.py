"""Audit log viewer endpoint.

Agency admins (and platform admins) can browse the immutable audit
log over a filter bar. Agency callers are always pinned to their own
agency_id; platform callers may pass any agency_id or none (= cross-
tenant view).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_platform_db
from app.core.permissions import require_permission
from app.core.pii_crypto import decrypt_pii
from app.models.agency import Agency
from app.models.audit_log import AuditLog
from app.models.client import Client
from app.models.user import User

router = APIRouter(tags=["audit"])

_PLATFORM_ROLES = {"platform_super_admin", "platform_admin"}


class AuditLogItem(BaseModel):
    id: int
    agency_id: Optional[uuid.UUID] = None
    agency_name: Optional[str] = None
    client_id: Optional[uuid.UUID] = None
    client_name: Optional[str] = None
    user_id: Optional[uuid.UUID] = None
    member_name: Optional[str] = None
    member_email: Optional[str] = None
    action: str
    resource_type: str
    resource_id: str
    request_path: Optional[str] = None
    request_method: Optional[str] = None
    status_code: Optional[int] = None
    success: bool
    ip_address: Optional[str] = None
    created_at: datetime
    extra_data: Optional[dict] = None


class MemberLite(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    agency_id: Optional[uuid.UUID] = None
    agency_name: Optional[str] = None


class ClientLite(BaseModel):
    id: uuid.UUID
    name: str
    agency_id: uuid.UUID
    agency_name: Optional[str] = None


class AuditLogPage(BaseModel):
    items: list[AuditLogItem]
    next_cursor: Optional[int] = None


@router.get("/audit-logs", response_model=AuditLogPage)
async def list_audit_logs(
    agency_id: Optional[uuid.UUID] = Query(default=None),
    client_id: Optional[uuid.UUID] = Query(default=None),
    user_id: Optional[uuid.UUID] = Query(default=None),
    event: Optional[str] = Query(default=None),
    since: Optional[datetime] = Query(default=None),
    until: Optional[datetime] = Query(default=None),
    success: Optional[bool] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    cursor: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_platform_db),
    user: User = Depends(require_permission("audit.read")),
) -> AuditLogPage:
    is_platform = user.role in _PLATFORM_ROLES
    stmt = select(AuditLog)

    # Tenant scope enforcement: non-platform users are pinned to their
    # own agency irrespective of the query param.
    if is_platform:
        if agency_id is not None:
            stmt = stmt.where(AuditLog.agency_id == agency_id)
    else:
        stmt = stmt.where(AuditLog.agency_id == user.agency_id)

    if client_id is not None:
        stmt = stmt.where(AuditLog.client_id == client_id)
    if user_id is not None:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if event:
        stmt = stmt.where(AuditLog.action.ilike(f"%{event}%"))
    if since is not None:
        stmt = stmt.where(AuditLog.created_at >= since)
    if until is not None:
        stmt = stmt.where(AuditLog.created_at <= until)
    if success is not None:
        stmt = stmt.where(AuditLog.success.is_(success))
    if cursor is not None:
        stmt = stmt.where(AuditLog.id < cursor)

    stmt = stmt.order_by(AuditLog.id.desc()).limit(limit + 1)
    rows = list((await db.execute(stmt)).scalars().all())

    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = rows[-1].id if has_more and rows else None

    # Resolve actor (user) + client + agency names in batch so the UI can
    # show readable labels instead of raw UUIDs. PII (email/full_name) is
    # already Fernet-encrypted on the User row; decrypt for display.
    user_ids = {r.user_id for r in rows if r.user_id}
    client_ids = {r.client_id for r in rows if r.client_id}
    agency_ids = {r.agency_id for r in rows if r.agency_id}

    users_map: dict[uuid.UUID, tuple[str, str]] = {}
    if user_ids:
        u_rows = (
            await db.execute(
                select(User.id, User.full_name, User.email).where(User.id.in_(user_ids))
            )
        ).all()
        for uid, full_name, email in u_rows:
            try:
                users_map[uid] = (decrypt_pii(full_name), decrypt_pii(email))
            except Exception:  # noqa: BLE001
                users_map[uid] = (str(full_name), str(email))

    clients_map: dict[uuid.UUID, str] = {}
    if client_ids:
        c_rows = (
            await db.execute(
                select(Client.id, Client.name).where(Client.id.in_(client_ids))
            )
        ).all()
        clients_map = {cid: name for cid, name in c_rows}

    agencies_map: dict[uuid.UUID, str] = {}
    if agency_ids:
        a_rows = (
            await db.execute(
                select(Agency.id, Agency.name).where(Agency.id.in_(agency_ids))
            )
        ).all()
        agencies_map = {aid: name for aid, name in a_rows}

    items = []
    for r in rows:
        member_name = member_email = None
        if r.user_id and r.user_id in users_map:
            member_name, member_email = users_map[r.user_id]
        items.append(
            AuditLogItem(
                id=r.id,
                agency_id=r.agency_id,
                agency_name=agencies_map.get(r.agency_id) if r.agency_id else None,
                client_id=r.client_id,
                client_name=clients_map.get(r.client_id) if r.client_id else None,
                user_id=r.user_id,
                member_name=member_name,
                member_email=member_email,
                action=r.action,
                resource_type=r.resource_type,
                resource_id=r.resource_id,
                request_path=r.request_path,
                request_method=r.request_method,
                status_code=r.status_code,
                success=r.success,
                ip_address=r.ip_address,
                created_at=r.created_at,
                extra_data=r.extra_data,
            )
        )
    return AuditLogPage(items=items, next_cursor=next_cursor)


@router.get("/audit-logs/members", response_model=list[MemberLite])
async def list_audit_members(
    db: AsyncSession = Depends(get_platform_db),
    user: User = Depends(require_permission("audit.read")),
) -> list[MemberLite]:
    """Members visible for filter dropdown.

    Platform-tier callers see every user across all agencies; Agency
    callers see only members of their own agency.
    """
    is_platform = user.role in _PLATFORM_ROLES
    stmt = select(User.id, User.full_name, User.email, User.agency_id, Agency.name).outerjoin(
        Agency, Agency.id == User.agency_id
    )
    if not is_platform:
        stmt = stmt.where(User.agency_id == user.agency_id)
    stmt = stmt.order_by(User.created_at.desc()).limit(2000)
    rows = (await db.execute(stmt)).all()
    out: list[MemberLite] = []
    for uid, fn, em, aid, an in rows:
        try:
            full = decrypt_pii(fn)
            email = decrypt_pii(em)
        except Exception:  # noqa: BLE001
            full, email = str(fn), str(em)
        out.append(
            MemberLite(id=uid, full_name=full, email=email, agency_id=aid, agency_name=an)
        )
    return out


@router.get("/audit-logs/clients", response_model=list[ClientLite])
async def list_audit_clients(
    db: AsyncSession = Depends(get_platform_db),
    user: User = Depends(require_permission("audit.read")),
) -> list[ClientLite]:
    """Clients visible for filter dropdown.

    Platform-tier callers see all clients across all agencies; Agency
    callers see only their own agency's clients.
    """
    is_platform = user.role in _PLATFORM_ROLES
    stmt = select(Client.id, Client.name, Client.agency_id, Agency.name).join(
        Agency, Agency.id == Client.agency_id
    )
    if not is_platform:
        stmt = stmt.where(Client.agency_id == user.agency_id)
    stmt = stmt.order_by(Client.created_at.desc()).limit(2000)
    rows = (await db.execute(stmt)).all()
    return [
        ClientLite(id=cid, name=cn, agency_id=aid, agency_name=an)
        for cid, cn, aid, an in rows
    ]
