"""Seed the RBAC permission catalogue + per-role defaults.

Run via:
    cd backend && set -a && . ../.env && set +a
    .venv/bin/python -m seeds.permissions_seed

Idempotent: uses INSERT ... ON CONFLICT DO NOTHING for permission rows
and an UPSERT for role defaults so re-running keeps defaults aligned
with the current source of truth in this file.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Iterable

from sqlalchemy import text

from app.core.database import PlatformSessionLocal
from app.models.user import UserRole

logger = logging.getLogger(__name__)


# ── Permission catalogue ─────────────────────────────────────────────────
# Format: (code, label, category, description)
PERMISSIONS: list[tuple[str, str, str, str]] = [
    # personas
    ("personas.read", "View personas", "personas", "Read access to persona records"),
    ("personas.write", "Manage personas", "personas", "Create or update personas"),
    ("personas.delete", "Delete personas", "personas", "Delete personas"),
    # creatives
    ("creatives.read", "View creatives", "creatives", "Read access to creative assets"),
    ("creatives.write", "Manage creatives", "creatives", "Create or update creatives"),
    ("creatives.generate", "Generate creatives", "creatives", "Trigger AI creative generation"),
    # campaigns
    ("campaigns.read", "View campaigns", "campaigns", "Read access to campaigns"),
    ("campaigns.write", "Manage campaigns", "campaigns", "Create or update campaigns"),
    ("campaigns.publish", "Publish campaigns", "campaigns", "Push campaigns live to ad platforms"),
    ("campaigns.budget.manage", "Manage campaign budgets", "campaigns", "Edit budget config"),
    # attribution
    ("attribution.read", "View attribution", "attribution", "Read attribution reports"),
    ("attribution.report.create", "Create attribution reports", "attribution", "Run new attribution analyses"),
    # reports
    ("reports.read", "View reports", "reports", "Read scheduled & ad-hoc reports"),
    ("reports.create", "Create reports", "reports", "Build new reports"),
    ("reports.export", "Export reports", "reports", "Download report files"),
    ("reports.schedule.manage", "Manage report schedules", "reports", "Schedule recurring reports"),
    # imports
    ("imports.upload", "Upload imports", "imports", "Upload CSV / file imports"),
    # team
    ("team.view", "View team", "team", "List team members"),
    ("team.invite", "Invite team members", "team", "Send team invitations"),
    ("team.deactivate", "Deactivate team members", "team", "Disable team accounts"),
    ("team.role.update", "Change team roles", "team", "Update a member's role"),
    # clients
    ("clients.view", "View clients", "clients", "List clients"),
    ("clients.create", "Create clients", "clients", "Add new clients"),
    ("clients.invite_viewer", "Invite client viewer", "clients", "Send portal invitations"),
    ("clients.delete", "Delete clients", "clients", "Remove a client"),
    # settings
    ("settings.view", "View settings", "settings", "View agency / account settings"),
    ("settings.edit_brand", "Edit brand settings", "settings", "Modify branding"),
    ("settings.edit_compliance", "Edit compliance settings", "settings", "Modify compliance config"),
    ("settings.permissions.manage", "Manage agency permissions", "settings", "Override permission defaults for this agency"),
    # integrations
    ("integrations.view", "View integrations", "integrations", "List connected integrations"),
    ("integrations.connect", "Connect integrations", "integrations", "Add new integrations"),
    ("integrations.disconnect", "Disconnect integrations", "integrations", "Remove integrations"),
    # audience_export
    ("audience_export.view", "View audience exports", "audience_export", "List audience exports"),
    ("audience_export.create", "Create audience exports", "audience_export", "Push audiences to ad platforms"),
    # portal
    ("portal.access", "Access client portal", "portal", "Read-only client portal access"),
    # notifications (referenced by sidebar)
    ("notifications.read", "View notifications", "notifications", "List user notifications"),
    # platform
    ("platform.agency.view", "View agencies", "platform", "List all agencies"),
    ("platform.agency.create", "Create agencies", "platform", "Provision new agencies"),
    ("platform.agency.suspend", "Suspend agencies", "platform", "Suspend an agency"),
    ("platform.agency.delete", "Delete agencies", "platform", "Destructive — delete an agency"),
    ("platform.agency.invite_admin", "Invite agency admins", "platform", "Send agency-admin invitations"),
    ("platform.users.view", "View platform users", "platform", "List platform-tier users"),
    ("platform.users.invite", "Invite platform users", "platform", "Send platform-tier invitations"),
    ("platform.permissions.manage", "Manage platform permissions", "platform", "Edit role permission defaults"),
    ("platform.audit.read", "Read audit log", "platform", "View the cross-tenant audit log"),
    # audit (agency-scoped)
    ("audit.read", "View audit log", "audit", "View the agency-scoped audit log"),
]


def _all_codes() -> set[str]:
    return {p[0] for p in PERMISSIONS}


def _by_category(*cats: str) -> set[str]:
    return {p[0] for p in PERMISSIONS if p[2] in cats}


def _exact(*codes: str) -> set[str]:
    return set(codes)


# ── Per-role default grants ──────────────────────────────────────────────
def _role_defaults() -> dict[UserRole, set[str]]:
    every = _all_codes()
    platform_admin_grants = every - {
        "platform.permissions.manage",
        "platform.agency.delete",
    }
    # Agency admin owns their tenant end-to-end, including configuring the
    # permission matrix and managing custom roles within their Agency.
    # `settings.permissions.manage` is what unlocks /settings/permissions
    # and /settings/roles in the sidebar.
    agency_admin_grants = (
        _by_category(
            "personas", "creatives", "campaigns", "attribution",
            "reports", "imports", "team", "clients",
            "integrations", "audience_export", "notifications",
            "settings",
        )
        | {"portal.access", "audit.read"}
    )
    agency_ops_grants = (
        _exact(
            "personas.read", "personas.write",
            "creatives.read", "creatives.write", "creatives.generate",
            "campaigns.read", "campaigns.write",
            "attribution.read", "attribution.report.create",
            "reports.read", "reports.create", "reports.export",
            "imports.upload",
            "integrations.view",
            "audience_export.view", "audience_export.create",
            "notifications.read",
            "settings.view",
            "team.view", "clients.view",
        )
    )
    client_viewer_grants = _exact(
        "portal.access", "reports.read", "personas.read",
    )
    return {
        UserRole.platform_super_admin: every,
        UserRole.platform_admin: platform_admin_grants,
        UserRole.agency_admin: agency_admin_grants,
        UserRole.agency_ops: agency_ops_grants,
        UserRole.client_viewer: client_viewer_grants,
    }


async def seed_permissions(session) -> dict[str, int]:
    """Upsert catalogue + role defaults. Returns summary counts."""
    # Catalogue: never override label/description here — INSERT ... DO NOTHING.
    await session.execute(
        text(
            """
            INSERT INTO public.permissions (code, label, category, description)
            VALUES (:code, :label, :category, :description)
            ON CONFLICT (code) DO NOTHING
            """
        ),
        [
            {"code": c, "label": l, "category": cat, "description": d}
            for (c, l, cat, d) in PERMISSIONS
        ],
    )

    # Defaults: upsert so changes to this file propagate on re-run.
    all_codes = _all_codes()
    defaults = _role_defaults()
    rows: list[dict] = []
    for role, granted_codes in defaults.items():
        for code in all_codes:
            rows.append(
                {
                    "role": role.value if hasattr(role, "value") else str(role),
                    "code": code,
                    "granted": code in granted_codes,
                }
            )
    await session.execute(
        text(
            """
            INSERT INTO public.role_permissions (role, permission_code, granted)
            VALUES (:role, :code, :granted)
            ON CONFLICT (role, permission_code)
            DO UPDATE SET granted = EXCLUDED.granted
            """
        ),
        rows,
    )
    await session.commit()

    counts = {(role.value if hasattr(role, "value") else str(role)): len(codes) for role, codes in defaults.items()}
    counts["__total_permissions__"] = len(all_codes)
    return counts


async def _main() -> None:
    logging.basicConfig(level=logging.INFO)
    async with PlatformSessionLocal() as session:
        summary = await seed_permissions(session)
    print("Seed complete.")
    print(f"Total permissions: {summary.pop('__total_permissions__')}")
    for role, n in summary.items():
        print(f"  {role}: {n} granted")


if __name__ == "__main__":
    asyncio.run(_main())
