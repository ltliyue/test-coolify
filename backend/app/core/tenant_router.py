"""Per-Agency AsyncEngine router.

PR 2 of the multi-tenant hardening plan moves every Agency onto its own
physical Postgres database. ``agencies.db_dsn`` is the source of truth.
This module owns the small connection-engine pool used to talk to those
per-tenant databases.

Design constraints:
* LRU capacity 64 engines (most installations have far fewer agencies;
  the cap is here so we cannot leak memory if many agencies churn).
* Idle eviction after 30 minutes of inactivity; the per-engine pool is
  ``pool_size=5, max_overflow=5`` so an unused engine still pins file
  descriptors and Postgres backends.
* Single process-wide singleton, lazy-init.

Audit / log emissions must use ``dsn_fingerprint(dsn)`` from
``app.core.dsn_fingerprint`` rather than the raw DSN.
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)


# LRU + idle-TTL parameters. Override in tests via the singleton if needed.
_MAX_ENGINES = 64
_IDLE_TTL_SECONDS = 30 * 60  # 30 minutes


class _Entry:
    __slots__ = ("engine", "sessionmaker", "last_used")

    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine
        self.sessionmaker = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        self.last_used = time.monotonic()


class TenantSessionRouter:
    """Process-wide singleton holding one AsyncEngine per agency."""

    _instance: Optional["TenantSessionRouter"] = None
    _instance_lock = asyncio.Lock()

    def __init__(self) -> None:
        self._engines: dict[uuid.UUID, _Entry] = {}
        # Per-agency lock so two concurrent first-uses don't double-create
        # the engine. Created lazily.
        self._creation_locks: dict[uuid.UUID, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    @classmethod
    def instance(cls) -> "TenantSessionRouter":
        if cls._instance is None:
            cls._instance = TenantSessionRouter()
        return cls._instance

    async def get_engine(self, agency_id: uuid.UUID, dsn: str) -> AsyncEngine:
        entry = self._engines.get(agency_id)
        if entry is not None:
            entry.last_used = time.monotonic()
            return entry.engine

        # Per-agency creation lock to avoid races on first use.
        async with self._global_lock:
            lock = self._creation_locks.setdefault(agency_id, asyncio.Lock())

        async with lock:
            entry = self._engines.get(agency_id)
            if entry is not None:
                entry.last_used = time.monotonic()
                return entry.engine

            await self._evict_if_needed()
            engine = create_async_engine(
                dsn,
                echo=False,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=5,
                pool_recycle=1800,
            )
            self._engines[agency_id] = _Entry(engine)
            logger.info(
                "tenant_router: created engine for agency=%s (pool=%d)",
                agency_id,
                len(self._engines),
            )
            return engine

    async def get_session(
        self, agency_id: uuid.UUID, dsn: str
    ) -> AsyncSession:
        """Return a fresh AsyncSession from the per-agency sessionmaker.

        The caller owns the session lifecycle (close / commit / rollback).
        """
        await self.get_engine(agency_id, dsn)
        entry = self._engines[agency_id]
        entry.last_used = time.monotonic()
        return entry.sessionmaker()

    async def dispose(self, agency_id: uuid.UUID) -> None:
        entry = self._engines.pop(agency_id, None)
        if entry is not None:
            try:
                await entry.engine.dispose()
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "tenant_router: dispose failed for %s: %s", agency_id, exc
                )

    async def dispose_all(self) -> None:
        ids = list(self._engines.keys())
        for agency_id in ids:
            await self.dispose(agency_id)
        logger.info("tenant_router: disposed all engines (%d)", len(ids))

    async def _evict_if_needed(self) -> None:
        """Evict idle/oldest engines until we're under the cap."""
        now = time.monotonic()
        # First pass: drop anything past the idle TTL.
        idle = [
            aid
            for aid, entry in self._engines.items()
            if now - entry.last_used > _IDLE_TTL_SECONDS
        ]
        for aid in idle:
            await self.dispose(aid)

        # Second pass: enforce hard cap.
        while len(self._engines) >= _MAX_ENGINES:
            oldest_aid = min(
                self._engines.items(), key=lambda kv: kv[1].last_used
            )[0]
            await self.dispose(oldest_aid)


__all__ = ["TenantSessionRouter"]
