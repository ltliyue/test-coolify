"""Permission administration endpoints (PR 3).

Platform-tier matrix (``/platform/permissions``) and Agency-tier matrix
(``/agencies/{agency_id}/permissions``). Both call into
``PermissionResolver.invalidate`` on mutation so cached effective
permission sets refresh on the next request.
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.audit import audit_event
from app.core.database import get_platform_db
from app.core.deps import get_current_user
from app.core.permissions import require_permission, resolver
from app.models.permission import (
    AgencyRolePermission,
    Permission,
    RolePermission,
)
from app.models.role import Role
from app.models.user import User

router = APIRouter(tags=["permissions"])


# ── Schemas ────────────────────────────────────────────────────────────────


class PermissionEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    code: str
    label: str
    category: str
    description: Optional[str] = None


class PlatformPermissionsResponse(BaseModel):
    role_defaults: dict[str, list[str]]
    all_permissions: list[PermissionEntry]


class PermissionUpdate(BaseModel):
    role: str
    code: str
    granted: bool


class AgencyPermissionsResponse(BaseModel):
    role_defaults: dict[str, list[str]]
    overrides: list[dict]  # {role, code, granted}
    effective: dict[str, list[str]]
    all_permissions: list[PermissionEntry]


async def _enforce_rank_below_caller(
    db: AsyncSession,
    *,
    caller_role: str,
    target_role: str,
    request: Request,
    actor: User,
    agency_id: Optional[uuid.UUID],
) -> None:
    """Reject when the caller tries to toggle perms on their own/superior role."""
    rows = (
        await db.execute(
            select(Role.code, Role.rank).where(
                Role.code.in_([caller_role, target_role])
            )
        )
    ).all()
    rank_map = {code: rank for code, rank in rows}
    caller_rank = int(rank_map.get(caller_role, 0))
    target_rank = int(rank_map.get(target_role, 0))
    if target_rank >= caller_rank:
        await audit_event(
            db=db,
            event="rbac.permission.denied_self_edit",
            actor=actor,
            agency_id=agency_id,
            resource=target_role,
            outcome="deny",
            after={
                "caller_role": caller_role,
                "caller_rank": caller_rank,
                "target_role": target_role,
                "target_rank": target_rank,
            },
            request=request,
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"cannot edit permissions for role '{target_role}': "
                "your role must rank strictly above the target."
            ),
        )


async def _ensure_role_exists(
    db: AsyncSession, role_code: str, agency_id: Optional[uuid.UUID] = None
) -> None:
    """Validate the role code exists in `roles` and is visible in scope.

    Platform scope (agency_id None): only roles where agency_id IS NULL.
    Agency scope: roles where agency_id IS NULL OR agency_id = :id.
    """
    row = (
        await db.execute(select(Role).where(Role.code == role_code))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unknown role: {role_code}",
        )
    if agency_id is None:
        if row.agency_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"role '{role_code}' is agency-scoped",
            )
    else:
        if row.agency_id is not None and row.agency_id != agency_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"role '{role_code}' is not visible in this agency",
            )


async def _load_catalogue(db: AsyncSession) -> list[PermissionEntry]:
    rows = (
        await db.execute(
            select(Permission).order_by(Permission.category, Permission.code)
        )
    ).scalars().all()
    return [PermissionEntry.model_validate(r) for r in rows]


async def _load_defaults(
    db: AsyncSession, role_codes: list[str]
) -> dict[str, list[str]]:
    rows = (
        await db.execute(
            select(RolePermission.role, RolePermission.permission_code).where(
                RolePermission.granted.is_(True)
            )
        )
    ).all()
    out: dict[str, list[str]] = {r: [] for r in role_codes}
    for role, code in rows:
        if role in out:
            out[role].append(code)
    for codes in out.values():
        codes.sort()
    return out


async def _list_visible_roles(
    db: AsyncSession, *, agency_id: Optional[uuid.UUID]
) -> list[Role]:
    """Roles visible in the matrix for this scope.

    * Platform view (agency_id=None): all roles where agency_id IS NULL.
    * Agency view: built-in / system roles with tier in (agency, client)
      that are agency_id IS NULL, plus Agency-scoped custom roles.
    """
    if agency_id is None:
        stmt = select(Role).where(Role.agency_id.is_(None)).order_by(Role.tier, Role.code)
    else:
        from sqlalchemy import or_, and_
        stmt = (
            select(Role)
            .where(
                or_(
                    and_(Role.agency_id.is_(None), Role.tier.in_(["agency", "client"])),
                    Role.agency_id == agency_id,
                )
            )
            .order_by(Role.tier, Role.code)
        )
    return list((await db.execute(stmt)).scalars().all())


# ── Platform-tier endpoints ────────────────────────────────────────────────


@router.get("/platform/permissions", response_model=PlatformPermissionsResponse)
async def list_platform_permissions(
    db: AsyncSession = Depends(get_platform_db),
    _admin: User = Depends(require_permission("platform.permissions.manage")),
) -> PlatformPermissionsResponse:
    catalogue = await _load_catalogue(db)
    visible_roles = await _list_visible_roles(db, agency_id=None)
    defaults = await _load_defaults(db, [r.code for r in visible_roles])
    return PlatformPermissionsResponse(
        role_defaults=defaults,
        all_permissions=catalogue,
    )


@router.put("/platform/permissions", status_code=status.HTTP_204_NO_CONTENT)
async def update_platform_permission(
    payload: PermissionUpdate,
    request: Request,
    db: AsyncSession = Depends(get_platform_db),
    admin: User = Depends(require_permission("platform.permissions.manage")),
) -> None:
    await _ensure_role_exists(db, payload.role, agency_id=None)
    await _enforce_rank_below_caller(
        db,
        caller_role=admin.role,
        target_role=payload.role,
        request=request,
        actor=admin,
        agency_id=None,
    )
    stmt = (
        pg_insert(RolePermission)
        .values(role=payload.role, permission_code=payload.code, granted=payload.granted)
        .on_conflict_do_update(
            index_elements=[RolePermission.role, RolePermission.permission_code],
            set_={"granted": payload.granted},
        )
    )
    await db.execute(stmt)
    await audit_event(
        db=db,
        event="rbac.permission.default_changed",
        actor=admin,
        agency_id=None,
        resource=f"{payload.role}:{payload.code}",
        after={"granted": payload.granted},
        request=request,
    )
    await db.commit()
    resolver.invalidate(role=payload.role)


# ── Agency-tier endpoints ──────────────────────────────────────────────────


async def _ensure_can_manage_agency(
    user: User,
    agency_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Allow platform.permissions.manage OR (settings.permissions.manage on own agency)."""
    perms = await resolver.effective_permissions(db, user.agency_id, user.role)
    if "platform.permissions.manage" in perms:
        return
    if "settings.permissions.manage" in perms and user.agency_id == agency_id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="missing permission to manage agency permissions",
    )


@router.get(
    "/agencies/{agency_id}/permissions", response_model=AgencyPermissionsResponse
)
async def list_agency_permissions(
    agency_id: uuid.UUID,
    db: AsyncSession = Depends(get_platform_db),
    user: User = Depends(get_current_user),
) -> AgencyPermissionsResponse:
    await _ensure_can_manage_agency(user, agency_id, db)
    catalogue = await _load_catalogue(db)
    visible_roles = await _list_visible_roles(db, agency_id=agency_id)
    role_codes = [r.code for r in visible_roles]
    defaults = await _load_defaults(db, role_codes)
    override_rows = (
        await db.execute(
            select(
                AgencyRolePermission.role,
                AgencyRolePermission.permission_code,
                AgencyRolePermission.granted,
            ).where(AgencyRolePermission.agency_id == agency_id)
        )
    ).all()
    overrides = [
        {"role": str(r), "code": c, "granted": g}
        for r, c, g in override_rows
    ]
    effective: dict[str, list[str]] = {}
    for code in role_codes:
        perms = await resolver.effective_permissions(db, agency_id, code)
        effective[code] = sorted(perms)
    return AgencyPermissionsResponse(
        role_defaults=defaults,
        overrides=overrides,
        effective=effective,
        all_permissions=catalogue,
    )


@router.put(
    "/agencies/{agency_id}/permissions", status_code=status.HTTP_204_NO_CONTENT
)
async def update_agency_permission(
    agency_id: uuid.UUID,
    payload: PermissionUpdate,
    request: Request,
    db: AsyncSession = Depends(get_platform_db),
    user: User = Depends(get_current_user),
) -> None:
    await _ensure_can_manage_agency(user, agency_id, db)
    await _ensure_role_exists(db, payload.role, agency_id=agency_id)
    await _enforce_rank_below_caller(
        db,
        caller_role=user.role,
        target_role=payload.role,
        request=request,
        actor=user,
        agency_id=agency_id,
    )
    stmt = (
        pg_insert(AgencyRolePermission)
        .values(
            agency_id=agency_id,
            role=payload.role,
            permission_code=payload.code,
            granted=payload.granted,
        )
        .on_conflict_do_update(
            index_elements=[
                AgencyRolePermission.agency_id,
                AgencyRolePermission.role,
                AgencyRolePermission.permission_code,
            ],
            set_={"granted": payload.granted},
        )
    )
    await db.execute(stmt)
    await audit_event(
        db=db,
        event="rbac.permission.agency_override",
        actor=user,
        agency_id=agency_id,
        resource=f"{payload.role}:{payload.code}",
        after={"granted": payload.granted},
        request=request,
    )
    await db.commit()
    resolver.invalidate(agency_id=agency_id, role=payload.role)
