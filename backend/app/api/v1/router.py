from __future__ import annotations
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.tenants import router as tenants_router
from app.api.v1.credentials import router as credentials_router
from app.api.v1.integrations import router as integrations_router
from app.api.v1.compliance import router as compliance_router
from app.api.v1.ai import router as ai_router
from app.api.v1.brands import router as brands_router
from app.api.v1.imports import router as imports_router
from app.api.v1.field_mappings import router as field_mappings_router
from app.api.v1.personas import router as personas_router
from app.api.v1.attribution import router as attribution_router
from app.api.v1.creatives import router as creatives_router
from app.api.v1.portal import router as portal_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.campaigns import router as campaigns_router
from app.api.v1.reports import router as reports_router
from app.api.v1.oauth_callback import router as oauth_router
from app.api.v1.team import router as team_router
from app.api.v1.platform import router as platform_router
from app.api.v1.permissions_admin import router as permissions_admin_router
from app.api.v1.roles_admin import router as roles_admin_router
from app.api.v1.audit_admin import router as audit_admin_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(tenants_router)
api_router.include_router(credentials_router)
api_router.include_router(integrations_router)
api_router.include_router(compliance_router)
api_router.include_router(ai_router)
api_router.include_router(brands_router)
api_router.include_router(imports_router)
api_router.include_router(field_mappings_router)
api_router.include_router(personas_router)
api_router.include_router(attribution_router)
api_router.include_router(creatives_router)
api_router.include_router(portal_router)
api_router.include_router(campaigns_router)
api_router.include_router(reports_router)
api_router.include_router(notifications_router)
api_router.include_router(oauth_router)
api_router.include_router(team_router)
api_router.include_router(platform_router)
api_router.include_router(permissions_admin_router)
api_router.include_router(roles_admin_router)
api_router.include_router(audit_admin_router)
