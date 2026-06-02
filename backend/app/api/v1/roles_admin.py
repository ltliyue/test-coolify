"""Custom role administration (PR 4).

Two scopes:

* ``/platform/roles`` — system-wide roles (``agency_id IS NULL``).
  Requires ``platform.permissions.manage``.
* ``/agencies/{agency_id}/roles`` — Agency-scoped custom roles plus
  read-only listing of system roles available for that Agency.
  Requires ``settings.permissions.manage`` on the caller's own Agency
  (or ``platform.permissions.manage``).

Built-in roles (``is_system=TRUE``) cannot be renamed or deleted. Custom
roles cannot be deleted if any user still holds them.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import or_, and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit_event
from app.core.database import get_platform_db
from app.core.deps import get_current_user
from app.core.permissions import require_permission, resolver
from app.core.role_codes import BUILTIN_ROLES
from app.models.role import Role
from app.models.user import User

router = APIRouter(tags=["roles"])

_VALID_TIERS = {"platform", "agency", "client"}
_AGENCY_TIERS = {"agency", "client"}
_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{2,63}$")


# ── Schemas ────────────────────────────────────────────────────────────────


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    code: str
    label: str
    tier: str
    agency_id: Optional[uuid.UUID] = None
    is_system: bool
    rank: int = 0
    description: Optional[str] = None
    created_at: datetime
    user_count: int = 0


class RoleCreate(BaseModel):
    code: str = Field(min_length=3, max_length=64)
    label: str = Field(min_length=1, max_length=120)
    tier: str
    rank: Optional[int] = Field(default=None, ge=0, le=999)
    description: Optional[str] = Field(default=None, max_length=500)


class RoleUpdate(BaseModel):
    label: Optional[str] = Field(default=None, min_length=1, max_length=120)
    rank: Optional[int] = Field(default=None, ge=0, le=999)
    description: Optional[str] = Field(default=None, max_length=500)


_TIER_DEFAULT_RANK = {"platform": 90, "agency": 35, "client": 5}


async def _caller_rank(db: AsyncSession, role_code: str) -> int:
    """Return the rank of the caller's current role (0 if unknown)."""
    row = (
        await db.execute(select(Role.rank).where(Role.code == role_code))
    ).first()
    return int(row[0]) if row else 0


def _ensure_rank_below(caller_rank: int, target_rank: int, detail: str) -> None:
    if target_rank >= caller_rank:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=detail
        )


# ── Helpers ────────────────────────────────────────────────────────────────


def _validate_code(code: str) -> None:
    if not _CODE_PATTERN.match(code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Role code must be lowercase a-z, digits and underscores, "
                "3-64 chars, starting with a letter"
            ),
        )


def _validate_tier(tier: str, *, allowed: set[str]) -> None:
    if tier not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"tier must be one of {sorted(allowed)}",
        )


async def _user_count(db: AsyncSession, role_code: str) -> int:
    return int(
        (
            await db.execute(
                select(func.count(User.id)).where(User.role == role_code)
            )
        ).scalar_one()
        or 0
    )


async def _get_role_or_404(
    db: AsyncSession, code: str, *, agency_id: Optional[uuid.UUID]
) -> Role:
    if agency_id is None:
        row = (
            await db.execute(
                select(Role).where(Role.code == code, Role.agency_id.is_(None))
            )
        ).scalar_one_or_none()
    else:
        row = (
            await db.execute(
                select(Role).where(Role.code == code, Role.agency_id == agency_id)
            )
        ).scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    return row


async def _serialize(db: AsyncSession, role: Role) -> RoleResponse:
    base = RoleResponse.model_validate(role)
    base.user_count = await _user_count(db, role.code)
    return base


async def _ensure_can_manage_agency_roles(
    user: User, agency_id: uuid.UUID, db: AsyncSession
) -> None:
    perms = await resolver.effective_permissions(db, user.agency_id, user.role)
    if "platform.permissions.manage" in perms:
        return
    if "settings.permissions.manage" in perms and user.agency_id == agency_id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="missing permission to manage agency roles",
    )


# ── Platform-scope endpoints ───────────────────────────────────────────────


@router.get("/platform/roles", response_model=list[RoleResponse])
async def list_platform_roles(
    db: AsyncSession = Depends(get_platform_db),
    _admin: User = Depends(require_permission("platform.permissions.manage")),
) -> list[RoleResponse]:
    rows = (
        await db.execute(
            select(Role).where(Role.agency_id.is_(None)).order_by(Role.tier, Role.code)
        )
    ).scalars().all()
    return [await _serialize(db, r) for r in rows]


@router.post(
    "/platform/roles",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_platform_role(
    payload: RoleCreate,
    request: Request,
    db: AsyncSession = Depends(get_platform_db),
    admin: User = Depends(require_permission("platform.permissions.manage")),
) -> RoleResponse:
    _validate_code(payload.code)
    _validate_tier(payload.tier, allowed=_VALID_TIERS)
    existing = (
        await db.execute(select(Role).where(Role.code == payload.code))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"role code already exists: {payload.code}",
        )
    caller_rank = await _caller_rank(db, admin.role)
    new_rank = payload.rank if payload.rank is not None else _TIER_DEFAULT_RANK[payload.tier]
    _ensure_rank_below(
        caller_rank, new_rank,
        f"cannot create a role at rank {new_rank} (your rank: {caller_rank})",
    )
    role = Role(
        code=payload.code,
        label=payload.label,
        tier=payload.tier,
        agency_id=None,
        is_system=False,
        rank=new_rank,
        description=payload.description,
        created_by=admin.id,
    )
    db.add(role)
    await db.flush()
    await audit_event(
        db=db,
        event="rbac.role.created",
        actor=admin,
        agency_id=None,
        resource=role.code,
        after={
            "code": role.code,
            "label": role.label,
            "tier": role.tier,
            "agency_id": None,
        },
        request=request,
    )
    await db.commit()
    await db.refresh(role)
    return await _serialize(db, role)


@router.patch("/platform/roles/{code}", response_model=RoleResponse)
async def update_platform_role(
    code: str,
    payload: RoleUpdate,
    request: Request,
    db: AsyncSession = Depends(get_platform_db),
    admin: User = Depends(require_permission("platform.permissions.manage")),
) -> RoleResponse:
    role = await _get_role_or_404(db, code, agency_id=None)
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Built-in roles cannot be modified",
        )
    caller_rank = await _caller_rank(db, admin.role)
    _ensure_rank_below(
        caller_rank, role.rank,
        "cannot manage a role at or above your own level",
    )
    if payload.rank is not None:
        _ensure_rank_below(
            caller_rank, payload.rank,
            f"cannot set rank to {payload.rank} (your rank: {caller_rank})",
        )
    before = {"label": role.label, "rank": role.rank, "description": role.description}
    if payload.label is not None:
        role.label = payload.label
    if payload.rank is not None:
        role.rank = payload.rank
    if payload.description is not None:
        role.description = payload.description
    await audit_event(
        db=db,
        event="rbac.role.updated",
        actor=admin,
        agency_id=None,
        resource=role.code,
        before=before,
        after={"label": role.label, "rank": role.rank, "description": role.description},
        request=request,
    )
    await db.commit()
    await db.refresh(role)
    return await _serialize(db, role)


@router.delete("/platform/roles/{code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_platform_role(
    code: str,
    request: Request,
    db: AsyncSession = Depends(get_platform_db),
    admin: User = Depends(require_permission("platform.permissions.manage")),
) -> None:
    role = await _get_role_or_404(db, code, agency_id=None)
    if role.is_system or code in BUILTIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Built-in roles cannot be deleted",
        )
    caller_rank = await _caller_rank(db, admin.role)
    _ensure_rank_below(
        caller_rank, role.rank,
        "cannot delete a role at or above your own level",
    )
    holders = await _user_count(db, code)
    if holders > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete: {holders} user(s) still hold this role",
        )
    await db.delete(role)
    await audit_event(
        db=db,
        event="rbac.role.deleted",
        actor=admin,
        agency_id=None,
        resource=code,
        before={"code": code, "label": role.label, "tier": role.tier},
        request=request,
    )
    await db.commit()
    resolver.invalidate(role=code)


# ── Agency-scope endpoints ─────────────────────────────────────────────────


@router.get(
    "/agencies/{agency_id}/roles", response_model=list[RoleResponse]
)
async def list_agency_roles(
    agency_id: uuid.UUID,
    db: AsyncSession = Depends(get_platform_db),
    user: User = Depends(get_current_user),
) -> list[RoleResponse]:
    await _ensure_can_manage_agency_roles(user, agency_id, db)
    rows = (
        await db.execute(
            select(Role)
            .where(
                or_(
                    and_(
                        Role.agency_id.is_(None),
                        Role.tier.in_(list(_AGENCY_TIERS)),
                    ),
                    Role.agency_id == agency_id,
                )
            )
            .order_by(Role.tier, Role.code)
        )
    ).scalars().all()
    return [await _serialize(db, r) for r in rows]


@router.post(
    "/agencies/{agency_id}/roles",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_agency_role(
    agency_id: uuid.UUID,
    payload: RoleCreate,
    request: Request,
    db: AsyncSession = Depends(get_platform_db),
    user: User = Depends(get_current_user),
) -> RoleResponse:
    await _ensure_can_manage_agency_roles(user, agency_id, db)
    _validate_code(payload.code)
    # Agency admins cannot create platform-tier roles.
    _validate_tier(payload.tier, allowed=_AGENCY_TIERS)
    existing = (
        await db.execute(select(Role).where(Role.code == payload.code))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"role code already exists: {payload.code}",
        )
    caller_rank = await _caller_rank(db, user.role)
    new_rank = payload.rank if payload.rank is not None else _TIER_DEFAULT_RANK[payload.tier]
    _ensure_rank_below(
        caller_rank, new_rank,
        f"cannot create a role at rank {new_rank} (your rank: {caller_rank})",
    )
    role = Role(
        code=payload.code,
        label=payload.label,
        tier=payload.tier,
        agency_id=agency_id,
        is_system=False,
        rank=new_rank,
        description=payload.description,
        created_by=user.id,
    )
    db.add(role)
    await db.flush()
    await audit_event(
        db=db,
        event="rbac.role.created",
        actor=user,
        agency_id=agency_id,
        resource=role.code,
        after={
            "code": role.code,
            "label": role.label,
            "tier": role.tier,
            "agency_id": str(agency_id),
        },
        request=request,
    )
    await db.commit()
    await db.refresh(role)
    return await _serialize(db, role)


@router.patch(
    "/agencies/{agency_id}/roles/{code}", response_model=RoleResponse
)
async def update_agency_role(
    agency_id: uuid.UUID,
    code: str,
    payload: RoleUpdate,
    request: Request,
    db: AsyncSession = Depends(get_platform_db),
    user: User = Depends(get_current_user),
) -> RoleResponse:
    await _ensure_can_manage_agency_roles(user, agency_id, db)
    role = await _get_role_or_404(db, code, agency_id=agency_id)
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Built-in roles cannot be modified",
        )
    caller_rank = await _caller_rank(db, user.role)
    _ensure_rank_below(
        caller_rank, role.rank,
        "cannot manage a role at or above your own level",
    )
    if payload.rank is not None:
        _ensure_rank_below(
            caller_rank, payload.rank,
            f"cannot set rank to {payload.rank} (your rank: {caller_rank})",
        )
    before = {"label": role.label, "rank": role.rank, "description": role.description}
    if payload.label is not None:
        role.label = payload.label
    if payload.rank is not None:
        role.rank = payload.rank
    if payload.description is not None:
        role.description = payload.description
    await audit_event(
        db=db,
        event="rbac.role.updated",
        actor=user,
        agency_id=agency_id,
        resource=role.code,
        before=before,
        after={"label": role.label, "rank": role.rank, "description": role.description},
        request=request,
    )
    await db.commit()
    await db.refresh(role)
    return await _serialize(db, role)


@router.delete(
    "/agencies/{agency_id}/roles/{code}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_agency_role(
    agency_id: uuid.UUID,
    code: str,
    request: Request,
    db: AsyncSession = Depends(get_platform_db),
    user: User = Depends(get_current_user),
) -> None:
    await _ensure_can_manage_agency_roles(user, agency_id, db)
    role = await _get_role_or_404(db, code, agency_id=agency_id)
    if role.is_system or code in BUILTIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Built-in roles cannot be deleted",
        )
    caller_rank = await _caller_rank(db, user.role)
    _ensure_rank_below(
        caller_rank, role.rank,
        "cannot delete a role at or above your own level",
    )
    holders = await _user_count(db, code)
    if holders > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete: {holders} user(s) still hold this role",
        )
    await db.delete(role)
    await audit_event(
        db=db,
        event="rbac.role.deleted",
        actor=user,
        agency_id=agency_id,
        resource=code,
        before={"code": code, "label": role.label, "tier": role.tier},
        request=request,
    )
    await db.commit()
    resolver.invalidate(agency_id=agency_id, role=code)
