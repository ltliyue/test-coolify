from __future__ import annotations
"""F-16 client portal API — to  client_viewer provideread-onlydataview。"""
import uuid
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.tenant_db import get_tenant_db
from app.core.permissions import require_permission
from app.models.user import User
from app.models.agency import Agency
from app.models.client import Client
from app.models.persona import Persona
from app.models.creative import Generation, GenerationResult
from app.models.attribution import AttributionReport

router = APIRouter(prefix="/portal", tags=["portal"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _brand_dict(raw: Optional[dict]) -> dict:
    """Extract portal-required fields from JSONB brand_config."""
    if not raw:
        return {}
    return {
        k: raw.get(k)
        for k in ("name", "logo_url", "primary_color", "secondary_color",
                   "industry", "tagline")
    }


# ── Response Schemas ──────────────────────────────────────────────────────────

class PortalBrandConfig(BaseModel):
    name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    industry: Optional[str] = None
    tagline: Optional[str] = None


class DashboardSummary(BaseModel):
    brand: PortalBrandConfig
    persona_count: int = 0
    creative_count: int = 0
    report_count: int = 0


class PortalPersona(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    recommended_tone: Optional[str] = None


class PortalCreative(BaseModel):
    id: uuid.UUID
    prompt: str
    status: str
    platforms: List[str] = []
    created_at: datetime


class PortalReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    report_type: str
    status: str
    created_at: datetime


# ── Internal ──────────────────────────────────────────────────────────────────

async def _resolve_brand(user: User, db: AsyncSession) -> dict:
    """For a caller bound to a client_id, prefer client.brand_config and
    fall back to the agency. RLS policy ``client_isolation`` enforces
    visibility separately at the row level.
    """
    if user.client_id is not None:
        client = await db.get(Client, user.client_id)
        if client and client.brand_config:
            return _brand_dict(client.brand_config)
    agency = await db.get(Agency, user.agency_id)
    return _brand_dict(agency.brand_config if agency else None)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=DashboardSummary)
async def portal_dashboard(
    user: User = Depends(require_permission("portal.access")),
    db: AsyncSession = Depends(get_tenant_db),
) -> DashboardSummary:
    """Client-portal dashboard summary.

    For a client_viewer with a bound client_id, attribution reports are
    further scoped down to that client_id (the only model in scope that
    carries a client_id column). Personas and creatives remain agency-
    shared by design (the Agency builds them once for all clients).
    """
    brand = await _resolve_brand(user, db)

    # RLS policy client_isolation handles client_id scoping
    persona_q = select(func.count(Persona.id)).where(
        Persona.agency_id == user.agency_id,
        Persona.is_active == True,  # noqa: E712
    )
    creative_q = select(func.count(Generation.id)).where(
        Generation.agency_id == user.agency_id,
    )
    report_q = select(func.count(AttributionReport.id)).where(
        AttributionReport.agency_id == user.agency_id,
    )

    persona_count = (await db.execute(persona_q)).scalar() or 0
    creative_count = (await db.execute(creative_q)).scalar() or 0
    report_count = (await db.execute(report_q)).scalar() or 0

    return DashboardSummary(
        brand=PortalBrandConfig(**brand),
        persona_count=persona_count,
        creative_count=creative_count,
        report_count=report_count,
    )


@router.get("/brand", response_model=PortalBrandConfig)
async def portal_brand(
    user: User = Depends(require_permission("portal.access")),
    db: AsyncSession = Depends(get_tenant_db),
) -> PortalBrandConfig:
    """get brand config (used forwhite-label theme）。"""
    brand = await _resolve_brand(user, db)
    return PortalBrandConfig(**brand)


@router.get("/personas", response_model=List[PortalPersona])
async def portal_personas(
    user: User = Depends(require_permission("portal.access")),
    db: AsyncSession = Depends(get_tenant_db),
) -> List[PortalPersona]:
    """clientvisible  personas（trimmed fields，does not expose model_used/source etc.internal info）。"""
    result = await db.execute(
        select(Persona)
        .where(
            Persona.agency_id == user.agency_id,
            Persona.is_active == True,  # noqa: E712
        )
        .order_by(Persona.created_at.desc())
        .limit(50)
    )
    return [PortalPersona.model_validate(p) for p in result.scalars().all()]


@router.get("/creatives", response_model=List[PortalCreative])
async def portal_creatives(
    user: User = Depends(require_permission("portal.access")),
    db: AsyncSession = Depends(get_tenant_db),
) -> List[PortalCreative]:
    """clientvisible  creatives（trimmed fields）。"""
    result = await db.execute(
        select(Generation)
        .where(Generation.agency_id == user.agency_id)
        .options(selectinload(Generation.results))
        .order_by(Generation.created_at.desc())
        .limit(20)
    )
    items: List[PortalCreative] = []
    for g in result.scalars().all():
        platforms = [
            r.platform.value if hasattr(r.platform, "value") else str(r.platform)
            for r in g.results
        ]
        items.append(PortalCreative(
            id=g.id,
            prompt=g.prompt,
            status=g.status.value if hasattr(g.status, "value") else str(g.status),
            platforms=platforms,
            created_at=g.created_at,
        ))
    return items


@router.get("/reports", response_model=List[PortalReport])
async def portal_reports(
    user: User = Depends(require_permission("portal.access")),
    db: AsyncSession = Depends(get_tenant_db),
) -> List[PortalReport]:
    """Client-visible attribution reports (trimmed fields).

    Scoped to the caller's agency, and further to the caller's client_id
    when the caller is a client_viewer with a bound client.
    """
    # RLS policy client_isolation handles client_id scoping
    q = (
        select(AttributionReport)
        .where(AttributionReport.agency_id == user.agency_id)
        .order_by(AttributionReport.created_at.desc())
        .limit(20)
    )
    result = await db.execute(q)
    return [PortalReport.model_validate(r) for r in result.scalars().all()]
