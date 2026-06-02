from __future__ import annotations
import os
import uuid
from typing import List, Optional
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_db import get_tenant_db
from app.core.deps import get_current_user
from app.models.report import ReportSchedule, ReportHistory
from app.models.user import User
from app.schemas.report import (
    ReportScheduleCreate, ReportScheduleUpdate, ReportScheduleResponse,
    ReportGenerateRequest, ReportHistoryResponse, ReportDownloadResponse,
    VALID_FREQUENCIES,
)

router = APIRouter(prefix="/reports", tags=["reports"])


def _schedule_to_response(s) -> ReportScheduleResponse:
    """Convert ORM object to response, computing recipients_count (does not expose plaintext email)."""
    count = 0
    if s.recipients_encrypted:
        try:
            from app.core.encryption import decrypt_credentials
            data = decrypt_credentials(s.recipients_encrypted)
            count = len(data.get("emails", []))
        except Exception:
            count = 0
    resp = ReportScheduleResponse.model_validate(s)
    resp.recipients_count = count
    return resp


# ── Schedule CRUD ─────────────────────────────────────────

@router.get("/schedules", response_model=List[ReportScheduleResponse])
async def list_schedules(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="report_schedule.list",
        actor=user,
        agency_id=user.agency_id,
    )
    stmt = select(ReportSchedule).where(
        ReportSchedule.agency_id == user.agency_id
    ).order_by(ReportSchedule.created_at.desc())
    result = await db.execute(stmt)
    return [_schedule_to_response(s) for s in result.scalars().all()]


@router.post("/schedules", response_model=ReportScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    body: ReportScheduleCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    # Compute the first run time
    now = datetime.now(timezone.utc)
    if body.frequency == "daily":
        next_run = now + timedelta(days=1)
    elif body.frequency == "weekly":
        next_run = now + timedelta(weeks=1)
    else:
        next_run = now + timedelta(days=30)

    # compliance rule 7：recipients to  PII，Fernet encrypt and store
    import json
    from app.core.encryption import encrypt_credentials
    recipients_encrypted = encrypt_credentials({"emails": body.recipients})

    schedule = ReportSchedule(
        agency_id=user.agency_id,
        client_id=body.client_id,
        schedule_name=body.schedule_name,
        frequency=body.frequency,
        recipients_encrypted=recipients_encrypted,
        metrics_config=body.metrics_config,
        brand_config_override=body.brand_config_override,
        next_run_at=next_run,
    )
    db.add(schedule)
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="report_schedule.create",
        actor=user,
        agency_id=user.agency_id,
    )
    await db.commit()
    await db.refresh(schedule)
    return _schedule_to_response(schedule)


@router.put("/schedules/{schedule_id}", response_model=ReportScheduleResponse)
async def update_schedule(
    schedule_id: uuid.UUID,
    body: ReportScheduleUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    result = await db.execute(
        select(ReportSchedule).where(
            ReportSchedule.id == schedule_id,
            ReportSchedule.agency_id == user.agency_id,
        )
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    UPDATABLE = {"schedule_name", "frequency", "recipients", "metrics_config", "brand_config_override", "is_active"}
    for field, value in body.model_dump(exclude_none=True).items():
        if field in UPDATABLE:
            setattr(schedule, field, value)
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="report_schedule.update",
        actor=user,
        agency_id=user.agency_id,
        resource=str(schedule_id,
    ))
    await db.commit()
    await db.refresh(schedule)
    return _schedule_to_response(schedule)


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    result = await db.execute(
        select(ReportSchedule).where(
            ReportSchedule.id == schedule_id,
            ReportSchedule.agency_id == user.agency_id,
        )
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="report_schedule.delete",
        actor=user,
        agency_id=user.agency_id,
        resource=str(schedule_id,
    ))
    await db.delete(schedule)
    await db.commit()


# ── Manual Report Generation ──────────────────────────────

@router.post("/generate", response_model=ReportHistoryResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(
    body: ReportGenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    """manually triggerone-off report generation。"""
    history = ReportHistory(
        agency_id=user.agency_id,
        client_id=body.client_id,
        report_type=body.report_type,
        status="pending",
    )
    db.add(history)
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="report.generate",
        actor=user,
        agency_id=user.agency_id,
    )
    await db.commit()
    await db.refresh(history)

    # Trigger async Celery task (skipped in test env)
    if os.getenv("TESTING") != "true":
        from app.tasks.report_tasks import generate_report_task
        generate_report_task.delay(str(history.id), str(user.agency_id))

    return ReportHistoryResponse.model_validate(history)


# ── Report History ────────────────────────────────────────

@router.get("/history", response_model=List[ReportHistoryResponse])
async def list_report_history(
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="report_history.list",
        actor=user,
        agency_id=user.agency_id,
    )
    stmt = select(ReportHistory).where(
        ReportHistory.agency_id == user.agency_id
    ).order_by(ReportHistory.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return [ReportHistoryResponse.model_validate(h) for h in result.scalars().all()]


@router.get("/history/{history_id}/download", response_model=ReportDownloadResponse)
async def download_report(
    history_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    result = await db.execute(
        select(ReportHistory).where(
            ReportHistory.id == history_id,
            ReportHistory.agency_id == user.agency_id,
        )
    )
    history = result.scalar_one_or_none()
    if not history:
        raise HTTPException(status_code=404, detail="Report not found")
    if not history.file_path:
        raise HTTPException(status_code=404, detail="Report file not available")

    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="report.download",
        actor=user,
        agency_id=user.agency_id,
        resource=str(history_id,
    ))
    await db.commit()

    from app.core.storage import get_presigned_url
    object_name = history.file_path.split("/", 1)[-1] if "/" in history.file_path else history.file_path
    url = get_presigned_url(object_name, expires_hours=24)
    if not url:
        raise HTTPException(status_code=503, detail="Storage temporarily unavailable")
    return ReportDownloadResponse(download_url=url)
