from __future__ import annotations
import uuid
from datetime import date as date_type
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_db import get_tenant_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.attribution import AttributionReport
from app.schemas.attribution import AttributionReportCreate, AttributionReportResponse

router = APIRouter(prefix="/attribution", tags=["attribution"])


@router.post("/report", response_model=AttributionReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_attribution_report(
    body: AttributionReportCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    from app.services.ai.context import build_shared_context
    from app.services.ai.agents import attribution as attribution_agent

    ctx = await build_shared_context(db, user.agency_id)

    if ctx.budget_remaining <= 0:
        raise HTTPException(status_code=429, detail="Monthly token budget exhausted")

    class _FakeReq:
        prompt = body.prompt
        agent = "attribution_reporting"
        agency_id = user.agency_id
        client_id = uuid.UUID(body.client_id) if body.client_id else None
        user_id = user.id
        context = {}
        request_id = str(uuid.uuid4())

    result = await attribution_agent.run(_FakeReq(), ctx)
    output = result.get("output", {})
    model_name = result.get("model", "")

    # parsedaterange
    dr_start = None
    dr_end = None
    if body.date_range_start:
        try:
            dr_start = date_type.fromisoformat(body.date_range_start)
        except ValueError:
            pass
    if body.date_range_end:
        try:
            dr_end = date_type.fromisoformat(body.date_range_end)
        except ValueError:
            pass

    report = AttributionReport(
        agency_id=user.agency_id,
        user_id=user.id,
        client_id=uuid.UUID(body.client_id) if body.client_id else None,
        title=body.title,
        report_type=body.report_type,
        date_range_start=dr_start,
        date_range_end=dr_end,
        channels=output.get("channels", []),
        results=output,
        insights="; ".join(output.get("recommendations", [])),
        model_used=model_name,
        status="completed",
    )
    db.add(report)
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="attribution.generate",
        actor=user,
        agency_id=user.agency_id,
    )
    await db.commit()
    await db.refresh(report)
    return AttributionReportResponse.model_validate(report)


@router.get("/reports", response_model=List[AttributionReportResponse])
async def list_reports(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    result = await db.execute(
        select(AttributionReport)
        .where(AttributionReport.agency_id == user.agency_id)
        .order_by(AttributionReport.created_at.desc())
        .limit(50)
    )
    return [AttributionReportResponse.model_validate(r) for r in result.scalars().all()]


@router.get("/reports/{report_id}", response_model=AttributionReportResponse)
async def get_report(
    report_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    result = await db.execute(
        select(AttributionReport).where(
            AttributionReport.id == report_id,
            AttributionReport.agency_id == user.agency_id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return AttributionReportResponse.model_validate(report)
