"""Permission resolution + ``require_permission`` FastAPI dependency.

PR 3 of the multi-tenant hardening plan. Replaces the role-based guards
in ``app.core.deps`` (now removed) with a configurable permission system.

Resolution order:

1. If ``(agency_id, role, code)`` row exists in
   ``agency_role_permissions`` → use that ``granted`` bool.
2. Otherwise → fall back to ``role_permissions`` for the same ``(role,
   code)``. Missing rows are treated as ``False``.

Effective permission sets are cached in-process for 5 minutes. Mutations
to either table must call :func:`PermissionResolver.invalidate` to clear
affected entries (see ``app.api.v1.permissions_admin``).

Enforcement mode is controlled by ``settings.RBAC_ENFORCEMENT_MODE``:

* ``"shadow"`` (default) — denied requests are allowed through but an
  audit row is written with ``rbac.permission.denied_shadow``.
* ``"enforce"`` — denied requests raise HTTP 403 and audit
  ``rbac.permission.denied_enforce``.
"""
from __future__ import annotations

import time
import uuid
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit_event
from app.core.config import settings
from app.core.database import get_platform_db
from app.core.deps import get_current_user
from app.models.permission import (
    AgencyRolePermission,
    Permission,
    RolePermission,
)
from app.models.user import User

_CACHE_TTL_SECONDS = 300


class PermissionResolver:
    """Process-level cache of effective permissions per ``(agency_id, role)``."""

    def __init__(self) -> None:
        # key: (agency_id_or_None, role_value)  -> (expires_at_ts, codes)
        self._cache: dict[tuple[Optional[uuid.UUID], str], tuple[float, set[str]]] = {}

    async def effective_permissions(
        self,
        db: AsyncSession,
        agency_id: Optional[uuid.UUID],
        role: str,
    ) -> set[str]:
        key = (agency_id, role)
        now = time.monotonic()
        cached = self._cache.get(key)
        if cached is not None and cached[0] > now:
            return cached[1]

        # Pull all permission codes (cheap — small catalogue).
        all_codes = {
            row[0] for row in (await db.execute(select(Permission.code))).all()
        }
        # Defaults for this role.
        defaults_rows = (
            await db.execute(
                select(RolePermission.permission_code, RolePermission.granted).where(
                    RolePermission.role == role
                )
            )
        ).all()
        defaults: dict[str, bool] = {code: granted for code, granted in defaults_rows}

        overrides: dict[str, bool] = {}
        if agency_id is not None:
            override_rows = (
                await db.execute(
                    select(
                        AgencyRolePermission.permission_code,
                        AgencyRolePermission.granted,
                    ).where(
                        AgencyRolePermission.agency_id == agency_id,
                        AgencyRolePermission.role == role,
                    )
                )
            ).all()
            overrides = {code: granted for code, granted in override_rows}

        effective: set[str] = set()
        for code in all_codes:
            if code in overrides:
                if overrides[code]:
                    effective.add(code)
            elif defaults.get(code, False):
                effective.add(code)

        self._cache[key] = (now + _CACHE_TTL_SECONDS, effective)
        return effective

    def invalidate(
        self,
        *,
        agency_id: Optional[uuid.UUID] = None,
        role: Optional[str] = None,
    ) -> None:
        """Clear cache entries matching the filters.

        If both filters are ``None`` the entire cache is cleared. A
        platform-default mutation passes ``role=...`` only; an agency
        override passes both ``agency_id`` and ``role``.
        """
        if agency_id is None and role is None:
            self._cache.clear()
            return
        keys_to_drop = []
        for key in self._cache:
            cached_agency, cached_role = key
            if agency_id is not None and cached_agency != agency_id:
                continue
            if role is not None and cached_role != role:
                continue
            keys_to_drop.append(key)
        for k in keys_to_drop:
            self._cache.pop(k, None)


# Process-level singleton.
resolver = PermissionResolver()


def require_permission(code: str):
    """FastAPI dependency factory enforcing a single permission code.

    Returns the current :class:`User`. In shadow mode denials still
    return the user so the endpoint behaves as before; the denial is
    captured in the audit log for later analysis.
    """

    async def _dep(
        request: Request,
        user: User = Depends(get_current_user),
        platform_db: AsyncSession = Depends(get_platform_db),
    ) -> User:
        perms = await resolver.effective_permissions(
            platform_db, user.agency_id, user.role
        )
        if code in perms:
            return user

        mode = (settings.RBAC_ENFORCEMENT_MODE or "shadow").lower()
        event_suffix = "denied_enforce" if mode == "enforce" else "denied_shadow"
        await audit_event(
            db=platform_db,
            event=f"rbac.permission.{event_suffix}",
            actor=user,
            agency_id=user.agency_id,
            resource=code,
            outcome="deny",
            after={
                "route": request.url.path,
                "method": request.method,
                "required_code": code,
            },
            request=request,
        )
        if mode == "enforce":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"missing permission: {code}",
            )
        return user

    return _dep


async def get_caller_permissions(
    user: User = Depends(get_current_user),
    platform_db: AsyncSession = Depends(get_platform_db),
) -> set[str]:
    """Helper for callers that want the full effective permission set."""
    return await resolver.effective_permissions(
        platform_db, user.agency_id, user.role.value
    )
