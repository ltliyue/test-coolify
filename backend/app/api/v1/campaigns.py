from __future__ import annotations
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_db import get_tenant_db
from app.core.deps import get_current_user
from app.core.warehouse_client import get_warehouse
from app.models.campaign import CampaignBudgetConfig
from app.models.user import User
from app.schemas.campaign import (
    BudgetConfigCreate, BudgetConfigUpdate, BudgetConfigResponse,
    CampaignMetric, CampaignSummary,
)
from app.services.campaign_query import CampaignQueryService, VALID_PLATFORMS

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


def _get_query_service() -> CampaignQueryService:
    return CampaignQueryService(get_warehouse())


# ── Campaign read-onlyquery（from warehouse） ─────────────────────────

@router.get("", response_model=List[CampaignMetric])
async def list_campaigns(
    platform: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    if platform and platform not in VALID_PLATFORMS:
        raise HTTPException(status_code=400, detail=f"Invalid platform. Valid: {VALID_PLATFORMS}")
    try:
        from app.core.audit import audit_event
        await audit_event(
        db=db,
        event="campaign.list",
        actor=user,
        agency_id=user.agency_id,
    )
        await db.commit()
        svc = _get_query_service()
        rows = svc.list_campaigns(
            str(user.agency_id), platform, client_id, date_from, date_to, limit, offset
        )
        return [CampaignMetric(**r) for r in rows]
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="Campaign data temporarily unavailable")


@router.get("/summary", response_model=CampaignSummary)
async def get_summary(
    client_id: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    view: str = Query("staff"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    try:
        from app.core.audit import audit_event
        await audit_event(
        db=db,
        event="campaign.summary",
        actor=user,
        agency_id=user.agency_id,
    )
        await db.commit()
        svc = _get_query_service()
        summary = svc.get_summary(str(user.agency_id), client_id, date_from, date_to)
        return CampaignSummary(**summary)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="Campaign data temporarily unavailable")


@router.get("/{platform}/{external_id}/metrics", response_model=List[CampaignMetric])
async def get_campaign_metrics(
    platform: str,
    external_id: str,
    limit: int = Query(90, ge=1, le=365),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    if platform not in VALID_PLATFORMS:
        raise HTTPException(status_code=400, detail=f"Invalid platform. Valid: {VALID_PLATFORMS}")
    try:
        from app.core.audit import audit_event
        await audit_event(
        db=db,
        event="campaign.metrics",
        actor=user,
        agency_id=user.agency_id,
    )
        await db.commit()
        svc = _get_query_service()
        rows = svc.get_campaign_metrics(str(user.agency_id), platform, external_id, limit, offset)
        return [CampaignMetric(**r) for r in rows]
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="Campaign data temporarily unavailable")


# ── Budget Config CRUD（PG） ────────────────────────────

@router.get("/budget-configs", response_model=List[BudgetConfigResponse])
async def list_budget_configs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="campaign_budget.list",
        actor=user,
        agency_id=user.agency_id,
    )
    stmt = select(CampaignBudgetConfig).where(
        CampaignBudgetConfig.agency_id == user.agency_id
    ).order_by(CampaignBudgetConfig.created_at.desc())
    result = await db.execute(stmt)
    return [BudgetConfigResponse.model_validate(c) for c in result.scalars().all()]


@router.post("/budget-configs", response_model=BudgetConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_budget_config(
    body: BudgetConfigCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    # UNIQUE constraintcheck
    existing = await db.execute(
        select(CampaignBudgetConfig).where(
            CampaignBudgetConfig.agency_id == user.agency_id,
            CampaignBudgetConfig.platform == body.platform,
            CampaignBudgetConfig.external_campaign_id == body.external_campaign_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Budget config already exists for this campaign")

    config = CampaignBudgetConfig(
        agency_id=user.agency_id,
        client_id=body.client_id,
        platform=body.platform,
        external_campaign_id=body.external_campaign_id,
        campaign_name=body.campaign_name,
        daily_budget=body.daily_budget,
        total_budget=body.total_budget,
        pacing_alert_threshold=body.pacing_alert_threshold,
        alert_enabled=body.alert_enabled,
    )
    db.add(config)
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="campaign_budget.create",
        actor=user,
        agency_id=user.agency_id,
    )
    await db.commit()
    await db.refresh(config)
    return BudgetConfigResponse.model_validate(config)


@router.put("/budget-configs/{config_id}", response_model=BudgetConfigResponse)
async def update_budget_config(
    config_id: uuid.UUID,
    body: BudgetConfigUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    result = await db.execute(
        select(CampaignBudgetConfig).where(
            CampaignBudgetConfig.id == config_id,
            CampaignBudgetConfig.agency_id == user.agency_id,
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Budget config not found")
    UPDATABLE_FIELDS = {"campaign_name", "daily_budget", "total_budget", "pacing_alert_threshold", "alert_enabled"}
    for field, value in body.model_dump(exclude_none=True).items():
        if field in UPDATABLE_FIELDS:
            setattr(config, field, value)
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="campaign_budget.update",
        actor=user,
        agency_id=user.agency_id,
        resource=str(config_id,
    ))
    await db.commit()
    await db.refresh(config)
    return BudgetConfigResponse.model_validate(config)


@router.delete("/budget-configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget_config(
    config_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    result = await db.execute(
        select(CampaignBudgetConfig).where(
            CampaignBudgetConfig.id == config_id,
            CampaignBudgetConfig.agency_id == user.agency_id,
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Budget config not found")
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="campaign_budget.delete",
        actor=user,
        agency_id=user.agency_id,
        resource=str(config_id,
    ))
    await db.delete(config)
    await db.commit()


# ── Budget Alerts（from notifications query） ────────────────

@router.get("/budget-alerts")
async def get_budget_alerts(
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="campaign_budget.alerts",
        actor=user,
        agency_id=user.agency_id,
    )
    from app.models.notification import Notification
    stmt = select(Notification).where(
        Notification.agency_id == user.agency_id,
        Notification.type == "budget_alert",
    ).order_by(Notification.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return [
        {
            "id": str(n.id),
            "title": n.title,
            "message": n.message,
            "metadata": n.metadata,
            "created_at": n.created_at.isoformat() if n.created_at else None,
            "is_read": n.is_read,
        }
        for n in result.scalars().all()
    ]
