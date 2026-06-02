"""Per-Agency database isolation.

PR 2 strategy: every Agency owns its own physical Postgres database.
``Agency.db_dsn`` is the source of truth; queries route through
:class:`app.core.tenant_router.TenantSessionRouter`.

There is **no** schema-per-Agency fallback any more — if an agency
row has ``db_dsn IS NULL`` the dependency raises a 500. The PR 2 data
migration (``backend/scripts/migrate_all_existing_agencies.py``)
guarantees every existing row has a DSN before migration 024 flips the
NOT NULL constraint.

Platform-scoped tables (``agencies``, ``users``, ``user_invitations``,
``audit_logs``, ``tenants``) stay on the platform engine and are read
through :func:`app.core.database.get_platform_db`.
"""
from __future__ import annotations

import logging
import uuid
from typing import AsyncIterator, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_platform_db
from app.core.deps import get_current_user
from app.core.tenant_router import TenantSessionRouter
from app.models.agency import Agency
from app.models.user import User

_log = logging.getLogger(__name__)


async def set_tenant_gucs(session: AsyncSession, user: User) -> None:
    """Set per-request GUCs that RLS policies in 023_client_rls.sql read.

    Sets the following transaction-local GUCs:

        app.role       — caller role string
        app.client_id  — caller client_id (empty when not bound)
        app.agency_id  — caller agency_id (empty for platform users)

    Missing GUCs cause the RLS policies to fall open (documented in
    023_client_rls.sql) which is correct for background jobs and
    platform users.
    """
    # SET LOCAL does not accept parameterized values; use set_config()
    # which is the parameterizable equivalent and respects transaction
    # scope when is_local=true.
    role_value = user.role.value if hasattr(user.role, "value") else str(user.role)
    await session.execute(
        text("SELECT set_config('app.role', :v, true)"), {"v": role_value}
    )
    await session.execute(
        text("SELECT set_config('app.client_id', :v, true)"),
        {"v": str(user.client_id) if user.client_id else ""},
    )
    await session.execute(
        text("SELECT set_config('app.agency_id', :v, true)"),
        {"v": str(user.agency_id) if user.agency_id else ""},
    )


async def get_tenant_db(
    user: User = Depends(get_current_user),
    platform_db: AsyncSession = Depends(get_platform_db),
) -> AsyncIterator[AsyncSession]:
    """Yield an AsyncSession bound to the caller's tenant DB.

    Platform users (``agency_id is None``) get a platform-scoped session
    instead — they have no tenant of their own. GUCs are still applied so
    RLS-protected platform queries (audit_logs, etc.) behave correctly.
    """
    if user.agency_id is None:
        await set_tenant_gucs(platform_db, user)
        _sample_guc_audit(user, None)
        yield platform_db
        return

    result = await platform_db.execute(
        select(Agency).where(Agency.id == user.agency_id)
    )
    agency = result.scalar_one_or_none()
    if agency is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Agency not found"
        )
    if not agency.db_dsn:
        # PR 2 invariant: every Agency must have its own DB after the
        # migration. Missing DSN is a configuration error, not a
        # recoverable state — fail loudly.
        _log.error(
            "agency %s has no db_dsn — provisioning is required", agency.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="tenant not provisioned",
        )

    session = await TenantSessionRouter.instance().get_session(
        agency.id, agency.db_dsn
    )
    try:
        await set_tenant_gucs(session, user)
        _sample_guc_audit(user, agency.id)
        yield session
    finally:
        await session.close()


def _sample_guc_audit(user: User, agency_id: Optional[uuid.UUID]) -> None:
    """Fire-and-forget 1% sampled audit for auth.session.guc_set."""
    from app.core.audit import audit_event, should_sample

    if not should_sample("auth.session.guc_set", 0.01):
        return
    import asyncio

    async def _emit() -> None:
        try:
            await audit_event(
                db=None,  # type: ignore[arg-type]
                event="auth.session.guc_set",
                actor=user,
                agency_id=agency_id,
                client_id=user.client_id,
                resource=None,
                outcome="ok",
            )
        except Exception as exc:  # noqa: BLE001
            _log.warning("sampled guc_set audit dropped: %s", exc)

    try:
        asyncio.get_running_loop().create_task(_emit())
    except RuntimeError:
        # No running loop (e.g. synchronous test setup); silently skip.
        pass


__all__ = ["get_tenant_db", "set_tenant_gucs"]
