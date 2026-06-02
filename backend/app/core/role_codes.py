"""Built-in role-code constants (PR 4).

Custom roles live in the ``roles`` table and are referenced by free-form
string codes. The constants here are kept for legacy callers and guard
clauses that need to compare against a built-in role without going to
the database.
"""
from __future__ import annotations

from types import SimpleNamespace

# String constants for the 5 built-in role codes. Use these instead of
# the previous `UserRole` enum members:
#   `UserRole.agency_admin`  -> `UserRole.agency_admin`  (same call site)
#   `UserRole.agency_admin.value` -> `UserRole.agency_admin` (already a str)
UserRole = SimpleNamespace(
    platform_super_admin="platform_super_admin",
    platform_admin="platform_admin",
    agency_admin="agency_admin",
    agency_ops="agency_ops",
    client_viewer="client_viewer",
)

BUILTIN_ROLES: frozenset[str] = frozenset(
    {
        "platform_super_admin",
        "platform_admin",
        "agency_admin",
        "agency_ops",
        "client_viewer",
    }
)

PLATFORM_ROLES: frozenset[str] = frozenset(
    {"platform_super_admin", "platform_admin"}
)

__all__ = ["UserRole", "BUILTIN_ROLES", "PLATFORM_ROLES"]
