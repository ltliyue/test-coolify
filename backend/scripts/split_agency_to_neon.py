#!/usr/bin/env python3
"""Migrate one Agency from the shared schema-per-Agency setup to a
dedicated per-tenant Postgres database (PR 2 cutover script).

Usage:
    split_agency_to_neon.py --agency-id <UUID> [--dry-run] [--mode managed_db|neon_api]

Workflow per agency:
  1. pg_dump the tenant_<slug> schema from the current shared cluster.
  2. Provision a new tenant DB via tenant_provisioner.
  3. Rewrite the dump to drop the schema prefix (-> public) and load it.
  4. Row-count parity check on all template tables.
  5. Update agencies.db_dsn (transactional, with db_dsn_previous backup).
  6. Audit start / complete / failed events.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import re
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Optional

# Make the backend/app package importable when running this script directly.
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "backend"))

from sqlalchemy import select, text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from app.core.audit import audit_event  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.database import PlatformSessionLocal  # noqa: E402
from app.core.dsn_fingerprint import dsn_fingerprint  # noqa: E402
from app.core.pii_crypto import decrypt_pii, encrypt_pii  # noqa: E402
from app.core.tenant_provisioner import provision_tenant_database  # noqa: E402
from app.models.agency import Agency  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("split_agency")


def _sync_admin_pgurl() -> str:
    """psql/pg_dump URL pointing at the shared platform cluster."""
    raw = settings.DATABASE_URL
    return raw.replace("postgresql+asyncpg://", "postgresql://").replace(
        "postgresql+psycopg2://", "postgresql://"
    )


def _pg_dump_schema(schema: str, out_path: Path) -> None:
    cmd = [
        "pg_dump",
        "--schema",
        schema,
        "--no-owner",
        "--no-privileges",
        "--file",
        str(out_path),
        _sync_admin_pgurl(),
    ]
    log.info("pg_dump %s -> %s", schema, out_path)
    subprocess.run(cmd, check=True)


def _rewrite_dump_to_public(dump_path: Path, schema: str) -> None:
    """Rewrite the dump so all references to ``schema.X`` become ``public.X``."""
    text_content = dump_path.read_text()
    new_lines: list[str] = []
    for line in text_content.splitlines():
        stripped = line.lstrip()
        # Drop CREATE SCHEMA <schema>; the new DB owns public already.
        if re.match(rf"\s*CREATE\s+SCHEMA\s+{re.escape(schema)}\b", line, re.IGNORECASE):
            continue
        # Drop pg_dump 18+ \restrict / \unrestrict directives — we use
        # --single-transaction so the restriction is unnecessary and
        # psql refuses other backslash commands while restricted.
        if stripped.startswith("\\restrict") or stripped.startswith("\\unrestrict"):
            continue
        if "search_path" in line.lower() and schema in line:
            new_lines.append(line.replace(schema, "public"))
            continue
        new_lines.append(line)
    rewritten = "\n".join(new_lines)
    # Replace any remaining schema-qualified references.
    rewritten = re.sub(rf"\b{re.escape(schema)}\.", "public.", rewritten)

    # Drop cross-DB FK constraints (REFERENCES public.{agencies,users,tenants}).
    # The platform tables don't exist in the per-Agency DB; referential
    # integrity is enforced at the application layer instead. The pattern
    # is a 2-line `ALTER TABLE ONLY ... ADD CONSTRAINT ... REFERENCES
    # public.<platform_table> ... ;` block.
    rewritten = re.sub(
        r"ALTER TABLE ONLY [^\n]+\n\s*ADD CONSTRAINT [a-zA-Z0-9_]+ FOREIGN KEY \([a-z_]+\) REFERENCES public\.(agencies|users|tenants)[^;]*;\n?",
        "",
        rewritten,
        flags=re.MULTILINE,
    )
    dump_path.write_text(rewritten)


def _psql_load(dump_path: Path, target_async_dsn: str) -> None:
    target_psql = target_async_dsn.replace("postgresql+asyncpg://", "postgresql://")
    cmd = ["psql", "--single-transaction", "--quiet", "--file", str(dump_path), target_psql]
    log.info("psql load -> dsn=%s", dsn_fingerprint(target_async_dsn))
    subprocess.run(cmd, check=True)


async def _count_rows(dsn: str, table: str) -> int:
    engine = create_async_engine(dsn)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text(f"SELECT count(*) FROM {table}"))
            return int(result.scalar_one())
    finally:
        await engine.dispose()


async def _tenant_tables(source_dsn: str, schema: str) -> list[str]:
    engine = create_async_engine(source_dsn)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = :s ORDER BY table_name"
                ),
                {"s": schema},
            )
            return [row[0] for row in result.fetchall()]
    finally:
        await engine.dispose()


async def _total_rows(dsn: str) -> int:
    tables = await _tenant_tables(dsn, "public")
    total = 0
    for t in tables:
        total += await _count_rows(dsn, f"public.{t}")
    return total


async def _parity_check(
    source_dsn: str, source_schema: str, target_dsn: str
) -> tuple[bool, list[tuple[str, int, int]]]:
    tables = await _tenant_tables(source_dsn, source_schema)
    mismatches: list[tuple[str, int, int]] = []
    for table in tables:
        src = await _count_rows(source_dsn, f"{source_schema}.{table}")
        tgt = await _count_rows(target_dsn, f"public.{table}")
        if src != tgt:
            mismatches.append((table, src, tgt))
    return (not mismatches), mismatches


async def split_one(agency_id: uuid.UUID, mode: str, dry_run: bool) -> int:
    async with PlatformSessionLocal() as platform_db:
        agency = await platform_db.get(Agency, agency_id)
        if agency is None:
            log.error("agency not found: %s", agency_id)
            return 2
        if agency.db_dsn:
            log.info(
                "agency %s already has db_dsn (fingerprint=%s) — skipping",
                agency_id,
                dsn_fingerprint(agency.db_dsn),
            )
            return 0

        os.environ["TENANT_PROVISION_MODE"] = mode
        # Force settings to re-read TENANT_PROVISION_MODE for this run.
        setattr(settings, "TENANT_PROVISION_MODE", mode)

        slug = agency.slug
        schema = agency.db_schema

        await audit_event(
            db=platform_db,
            event="tenant.migration.start",
            actor=None,
            agency_id=agency.id,
            resource=str(agency.id),
            after={"mode": mode, "schema": schema, "dry_run": dry_run},
        )

        with tempfile.TemporaryDirectory() as tmp:
            dump_path = Path(tmp) / f"{slug}.sql"
            try:
                _pg_dump_schema(schema, dump_path)
                _rewrite_dump_to_public(dump_path, schema)

                if dry_run:
                    log.info(
                        "[dry-run] would provision DB for %s and load dump (%d bytes)",
                        slug,
                        dump_path.stat().st_size,
                    )
                    return 0

                # apply_schema=False: the pg_dump carries DDL + data; the
                # provisioner would otherwise create the same tables twice
                # and psql --single-transaction would hang on duplicate
                # CREATE TABLE inside an aborted transaction.
                encrypted_dsn = await provision_tenant_database(
                    agency=agency,
                    platform_db=platform_db,
                    apply_schema=False,
                )
                raw_dsn = decrypt_pii(encrypted_dsn)
                _psql_load(dump_path, raw_dsn)

                ok, mismatches = await _parity_check(
                    settings.DATABASE_URL, schema, raw_dsn
                )
                if not ok:
                    log.error("parity check failed: %s", mismatches)
                    await audit_event(
                        db=platform_db,
                        event="tenant.migration.failed",
                        actor=None,
                        agency_id=agency.id,
                        resource=str(agency.id),
                        outcome="error",
                        after={"mismatches": mismatches},
                    )
                    return 3

                # Smoke query.
                count = await _count_rows(raw_dsn, "public.personas")
                log.info("smoke query: personas count = %d", count)

                # Persist DSN switch.
                await platform_db.execute(
                    text(
                        "UPDATE agencies SET db_dsn_previous = db_dsn, "
                        "db_dsn = :d WHERE id = :i"
                    ),
                    {"d": encrypt_pii(raw_dsn), "i": agency.id},
                )
                await audit_event(
                    db=platform_db,
                    event="tenant.migration.complete",
                    actor=None,
                    agency_id=agency.id,
                    resource=str(agency.id),
                    after={
                        "dsn_fingerprint": dsn_fingerprint(raw_dsn),
                        "row_count_total": await _total_rows(raw_dsn),
                    },
                )
                await platform_db.commit()
                log.info("agency %s migrated successfully", slug)
                return 0
            except Exception as exc:  # noqa: BLE001
                log.exception("migration failed: %s", exc)
                try:
                    await audit_event(
                        db=platform_db,
                        event="tenant.migration.failed",
                        actor=None,
                        agency_id=agency.id,
                        resource=str(agency.id),
                        outcome="error",
                        after={"error": str(exc)[:500]},
                    )
                    await platform_db.commit()
                except Exception:  # noqa: BLE001
                    pass
                return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agency-id", required=True, type=uuid.UUID)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--mode",
        choices=["managed_db", "neon_api"],
        default="managed_db",
    )
    args = parser.parse_args()
    return asyncio.run(split_one(args.agency_id, args.mode, args.dry_run))


if __name__ == "__main__":
    sys.exit(main())
