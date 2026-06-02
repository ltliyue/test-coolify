"""Platform database engine.

PR 2 splits the database story:

* ``platform_engine`` / ``PlatformSessionLocal`` — bound to the platform
  database (``settings.DATABASE_URL``). Owns ``agencies``, ``users``,
  ``user_invitations``, ``audit_logs``, ``tenants``, ``platform_roles``,
  ``token_usage``, etc.
* Per-Agency engines live in :mod:`app.core.tenant_router`. Tenant-scoped
  routes depend on :func:`app.core.tenant_db.get_tenant_db` instead of
  :func:`get_platform_db` below.

The legacy ``engine`` / ``async_session`` / ``get_db`` names are kept as
aliases pointing at the platform pair so the audit module (PR 1) and any
not-yet-migrated callers continue to work; they are platform-only.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

platform_engine = create_async_engine(
    settings.DATABASE_URL, echo=False, pool_pre_ping=True
)
PlatformSessionLocal = async_sessionmaker(
    platform_engine, class_=AsyncSession, expire_on_commit=False
)

# Legacy aliases — platform-only. Do NOT introduce new callers; new code
# should depend on get_platform_db (platform) or get_tenant_db (tenant).
engine = platform_engine
async_session = PlatformSessionLocal


class Base(DeclarativeBase):
    pass


async def get_platform_db():
    """FastAPI dependency yielding a session bound to the platform DB."""
    async with PlatformSessionLocal() as session:
        yield session


# Legacy alias retained for callers we have not migrated yet (notably the
# audit module's platform sessionmaker import path and a few platform
# routers). Tenant-scoped routers MUST switch to get_tenant_db.
get_db = get_platform_db
