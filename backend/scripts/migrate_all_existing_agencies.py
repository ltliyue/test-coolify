#!/usr/bin/env python3
"""Migrate every Agency with a NULL db_dsn to a per-tenant database.

Wraps ``split_agency_to_neon.split_one`` and runs it sequentially over
every Agency that still has ``db_dsn IS NULL``. Required as part of the
PR 2 cutover before applying ``024_agency_db_dsn_required.sql``.

Usage:
    migrate_all_existing_agencies.py --dry-run
    migrate_all_existing_agencies.py --execute [--mode managed_db|neon_api]
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "backend"))

from sqlalchemy import select  # noqa: E402

from app.core.database import PlatformSessionLocal  # noqa: E402
from app.models.agency import Agency  # noqa: E402

from split_agency_to_neon import split_one  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("migrate_all")


async def run(dry_run: bool, mode: str) -> int:
    async with PlatformSessionLocal() as db:
        result = await db.execute(
            select(Agency).where(Agency.db_dsn.is_(None)).order_by(Agency.created_at)
        )
        agencies = result.scalars().all()
        if not agencies:
            log.info("nothing to migrate — every agency already has db_dsn set")
            return 0
        log.info("found %d agencies pending migration", len(agencies))
        rc = 0
        for agency in agencies:
            log.info("--- migrating %s (id=%s)", agency.slug, agency.id)
            r = await split_one(agency.id, mode=mode, dry_run=dry_run)
            if r != 0:
                rc = r
                log.error("aborting batch because %s failed", agency.slug)
                break
        return rc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true")
    group.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--mode",
        choices=["managed_db", "neon_api"],
        default="managed_db",
    )
    args = parser.parse_args()
    return asyncio.run(run(args.dry_run, args.mode))


if __name__ == "__main__":
    sys.exit(main())
