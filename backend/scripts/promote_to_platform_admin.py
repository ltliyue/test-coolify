"""Promote a user to platform_super_admin.

Usage:
    python scripts/promote_to_platform_admin.py --email someone@example.com
    python scripts/promote_to_platform_admin.py --first

The script is idempotent: running it again on an already-promoted user
is a no-op (still prints the user id).

Note: PII (email) is Fernet-encrypted in the database. We resolve a user
by SHA-256 ``email_hash`` when ``--email`` is supplied; otherwise we pick
the oldest user by ``created_at ASC`` via ``--first``.

The promotion sets ``role=platform_super_admin`` and ``agency_id=NULL``.
The user's previous agency is left untouched (other agency members can
still access it). A warning is printed if the user formerly had an
agency_id.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Make `app` importable when running this script from backend/
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import async_session  # noqa: E402
from app.core.pii_crypto import hash_email  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402


async def _find_user(db: AsyncSession, email: Optional[str], pick_first: bool) -> Optional[User]:
    if email:
        result = await db.execute(
            select(User).where(User.email_hash == hash_email(email))
        )
        return result.scalar_one_or_none()
    if pick_first:
        result = await db.execute(select(User).order_by(User.created_at.asc()).limit(1))
        return result.scalar_one_or_none()
    return None


async def _promote(email: Optional[str], pick_first: bool) -> int:
    async with async_session() as db:  # type: AsyncSession
        user = await _find_user(db, email, pick_first)
        if user is None:
            print("No matching user found.", file=sys.stderr)
            return 1

        prior_agency_id: Optional[uuid.UUID] = user.agency_id
        already = (
            user.role == UserRole.platform_super_admin
            and user.agency_id is None
        )
        user.role = UserRole.platform_super_admin
        user.agency_id = None
        await db.commit()
        await db.refresh(user)

        if already:
            print(f"User {user.id} is already a platform_super_admin (no-op).")
        else:
            print(f"Promoted user {user.id} to platform_super_admin.")
            if prior_agency_id is not None:
                print(
                    f"WARNING: user previously belonged to agency {prior_agency_id}. "
                    "That agency was left untouched; other members retain access."
                )
        return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote a user to platform_super_admin")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--email", help="Email of the user to promote")
    group.add_argument(
        "--first",
        action="store_true",
        help="Promote the oldest user (lowest created_at)",
    )
    args = parser.parse_args()
    rc = asyncio.run(_promote(args.email, args.first))
    sys.exit(rc)


if __name__ == "__main__":
    main()
