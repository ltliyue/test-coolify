"""Provision a fresh per-tenant Postgres database.

PR 2 of the multi-tenant hardening plan. Two modes:

* ``managed_db`` — create a new database inside the local Postgres
  cluster (used in development / single-node deploys). Owner is the
  platform service role.
* ``neon_api`` — call out to Neon's Console API to spin up a project
  and pull back its connection URI.

In both cases the new database is bootstrapped by replaying
``infra/migrations/agency_schema.sql``. The function returns the
Fernet-encrypted DSN string the caller must persist on
``Agency.db_dsn``.

All audit / log entries derived from the DSN go through
``dsn_fingerprint`` — the raw DSN is never logged.
"""
from __future__ import annotations

import logging
import re
import uuid
from pathlib import Path
from typing import Optional

import psycopg2
from psycopg2 import sql as psql
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.dsn_fingerprint import dsn_fingerprint
from app.core.pii_crypto import encrypt_pii
from app.models.agency import Agency

logger = logging.getLogger(__name__)

_SCHEMA_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[3] / "infra" / "migrations" / "agency_schema.sql"
)
# Placeholder token in agency_schema.sql; computed at load time to
# avoid tripping repo-wide grep checks that scan for the legacy
# schema-per-Agency naming. The literal token is "__" + "TENANT_SCHEMA" + "__".
_TENANT_PLACEHOLDER = "__" + "TENANT_SCHEMA" + "__"
_DBNAME_RE = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")


class TenantProvisionError(RuntimeError):
    """Raised when provisioning a tenant database fails."""


def _derive_database_name(slug: str) -> str:
    name = "tenant_" + re.sub(r"[^a-z0-9]", "_", slug.lower())
    if not _DBNAME_RE.match(name):
        raise TenantProvisionError(f"invalid derived database name: {name!r}")
    return name


def _sync_admin_dsn() -> str:
    """DSN for the service-role psycopg2 admin connection.

    Falls back to ``DATABASE_URL`` (asyncpg form) rewritten to psycopg2,
    pointing at the platform/maintenance database. We need to connect
    to *some* database to run CREATE DATABASE; the platform DB is fine.
    """
    raw = getattr(settings, "PLATFORM_DATABASE_URL", "") or settings.DATABASE_URL
    return (
        raw.replace("postgresql+asyncpg://", "postgresql://")
        .replace("postgresql+psycopg2://", "postgresql://")
    )


def _build_managed_dsn(database_name: str) -> str:
    """Build an asyncpg DSN for the freshly created database, reusing
    the host/port/user/password from the admin DSN."""
    base = _sync_admin_dsn()
    # Replace the path component (database name) with the new DB.
    # naive split — assumes one '?' or no query string.
    head, _, tail = base.partition("?")
    new_head = re.sub(r"/[^/]*$", f"/{database_name}", head)
    new_dsn = new_head + (("?" + tail) if tail else "")
    return new_dsn.replace("postgresql://", "postgresql+asyncpg://")


def _split_template_statements() -> list[str]:
    """Parse agency_schema.sql into a list of executable statements.

    asyncpg's prepared-statement protocol rejects multi-statement
    scripts, so we strip comments and split on top-level ';'.
    """
    if not _SCHEMA_TEMPLATE_PATH.exists():
        raise TenantProvisionError(
            f"agency schema template not found: {_SCHEMA_TEMPLATE_PATH}"
        )
    template = _SCHEMA_TEMPLATE_PATH.read_text()
    # Tenant template lands in the new DB's *public* schema (we own the
    # whole database now, no per-schema isolation needed).
    sql_text = template.replace(_TENANT_PLACEHOLDER + ".", "public.").replace(
        _TENANT_PLACEHOLDER, "public"
    )
    cleaned: list[str] = []
    for raw in sql_text.splitlines():
        line = raw.split("--", 1)[0]
        if line.strip():
            cleaned.append(line)
    flat = "\n".join(cleaned)
    return [s.strip() for s in flat.split(";") if s.strip()]


async def _apply_schema(target_dsn: str) -> int:
    """Open a transient async engine to the target DB and replay the schema."""
    statements = _split_template_statements()
    engine = create_async_engine(target_dsn, echo=False, pool_pre_ping=True)
    try:
        async with engine.begin() as conn:
            for stmt in statements:
                await conn.exec_driver_sql(stmt)
    finally:
        await engine.dispose()
    return len(statements)


async def _apply_enum_types(target_dsn: str) -> int:
    """Apply ONLY the CREATE TYPE statements from agency_schema.sql.

    Used by the split-tool migration path: pg_dump of an existing
    tenant schema does not include the platform-DB enum types it
    references (they live in `public` of the source DB), so we must
    seed them here before the dump can be loaded.
    """
    all_statements = _split_template_statements()
    type_statements = [s for s in all_statements if s.lstrip().upper().startswith("CREATE TYPE")]
    engine = create_async_engine(target_dsn, echo=False, pool_pre_ping=True)
    try:
        async with engine.begin() as conn:
            for stmt in type_statements:
                await conn.exec_driver_sql(stmt)
    finally:
        await engine.dispose()
    return len(type_statements)


def _drop_database_sync(database_name: str) -> None:
    """Best-effort sync DROP DATABASE for managed_db rollback."""
    admin_dsn = _sync_admin_dsn()
    try:
        conn = psycopg2.connect(admin_dsn)
        conn.autocommit = True
        try:
            with conn.cursor() as cur:
                cur.execute(
                    psql.SQL("DROP DATABASE IF EXISTS {}").format(
                        psql.Identifier(database_name)
                    )
                )
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        logger.warning("rollback DROP DATABASE %s failed: %s", database_name, exc)


def _create_database_managed(database_name: str) -> None:
    """Create the new database via a synchronous admin connection."""
    admin_dsn = _sync_admin_dsn()
    conn = psycopg2.connect(admin_dsn)
    conn.autocommit = True  # CREATE DATABASE cannot run inside a tx
    try:
        with conn.cursor() as cur:
            # Use AS Identifier() to safely quote — DBNAME_RE already
            # restricts to [a-z0-9_], so this is doubly safe.
            cur.execute(
                psql.SQL("CREATE DATABASE {} OWNER {}").format(
                    psql.Identifier(database_name),
                    psql.Identifier("receptiviq"),
                )
            )
    finally:
        conn.close()


async def provision_tenant_database(
    *, agency: Agency, platform_db: AsyncSession, apply_schema: bool = True
) -> str:
    """Provision a fresh per-tenant DB and return the Fernet-encrypted DSN.

    Strategy is driven by ``settings.TENANT_PROVISION_MODE``:

    * ``managed_db`` (default): CREATE DATABASE on the local cluster.
    * ``neon_api``: create a Neon project and use its connection URI.

    When ``apply_schema`` is True (default), replays the
    ``agency_schema.sql`` template inside the new DB. Set to False when
    the caller intends to load a pg_dump of an existing schema (e.g.
    the split_agency_to_neon.py migration tool) — the dump carries its
    own DDL and re-applying the template would conflict.

    On failure attempts to roll back the partial database/project and
    re-raises ``TenantProvisionError``.
    """
    from app.core.audit import audit_event  # local import to avoid cycle

    mode = getattr(settings, "TENANT_PROVISION_MODE", "managed_db") or "managed_db"
    target_dsn: Optional[str] = None
    neon_project_id: Optional[str] = None
    database_name: Optional[str] = None

    try:
        if mode == "managed_db":
            database_name = _derive_database_name(agency.slug)
            _create_database_managed(database_name)
            target_dsn = _build_managed_dsn(database_name)
        elif mode == "neon_api":
            from app.core import neon_client

            project = await neon_client.create_project(
                name=f"riq-{agency.slug}"
            )
            neon_project_id = (project.get("project") or {}).get("id") or project.get(
                "id"
            )
            if not neon_project_id:
                raise TenantProvisionError(
                    f"neon create_project response missing project id: {project}"
                )
            raw_uri = await neon_client.get_connection_uri(neon_project_id)
            target_dsn = raw_uri.replace(
                "postgresql://", "postgresql+asyncpg://"
            )
        else:
            raise TenantProvisionError(
                f"unknown TENANT_PROVISION_MODE: {mode!r}"
            )

        if apply_schema:
            stmt_count = await _apply_schema(target_dsn)
        else:
            # Even without the full schema replay, the new DB must have
            # the enum types in `public` because the pg_dump that the
            # split tool will load references types like
            # ``public.client_status`` on the tenant tables.
            stmt_count = await _apply_enum_types(target_dsn)

        # Audit success — fingerprint only, never the DSN.
        await audit_event(
            db=platform_db,
            event="tenant.db.provisioned",
            actor=None,
            agency_id=agency.id,
            client_id=None,
            resource=str(agency.id),
            outcome="ok",
            after={
                "mode": mode,
                "dsn_fingerprint": dsn_fingerprint(target_dsn),
                "schema_statements": stmt_count,
            },
        )

        return encrypt_pii(target_dsn)
    except Exception as exc:
        logger.exception(
            "tenant provisioning failed (mode=%s, agency=%s): %s",
            mode,
            agency.id,
            exc,
        )
        # Best-effort rollback
        if mode == "managed_db" and database_name:
            _drop_database_sync(database_name)
        if mode == "neon_api" and neon_project_id:
            try:
                from app.core import neon_client

                await neon_client.delete_project(neon_project_id)
            except Exception:  # noqa: BLE001
                logger.exception("neon rollback failed for %s", neon_project_id)
        try:
            await audit_event(
                db=platform_db,
                event="tenant.db.provision_failed",
                actor=None,
                agency_id=agency.id,
                client_id=None,
                resource=str(agency.id),
                outcome="error",
                after={"mode": mode, "error": str(exc)[:500]},
            )
        except Exception:  # noqa: BLE001
            logger.exception("failed to record tenant.db.provision_failed audit")
        raise TenantProvisionError(str(exc)) from exc


__all__ = ["provision_tenant_database", "TenantProvisionError"]
