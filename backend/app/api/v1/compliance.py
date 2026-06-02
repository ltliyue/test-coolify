from __future__ import annotations
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.compliance.anonymizer import hash_identifier
from app.core.tenant_db import get_tenant_db
from typing import Optional


def _truncate_ip(ip: Optional[str]) -> Optional[str]:
    """M-04: Truncate IP to /24 subnet (HIPAA Safe Harbor — IP is a PHI identifier)."""
    if not ip:
        return None
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.{parts[2]}.0"
    # IPv6 or other format: truncate the second half
    if ":" in ip:
        segments = ip.split(":")
        return ":".join(segments[:4]) + "::0"
    return ip
from app.core.deps import get_current_user
from app.models.consent import ConsentRecord
from app.models.dsar import DSARRequest
from app.models.enums import ConsentPurpose, DSARStatus, Regulation
from app.models.user import User
from app.schemas.compliance import (
    ConsentCreate,
    ConsentResponse,
    ConsentWithdraw,
    DSARCreate,
    DSARResponse,
    DSARUpdateStatus,
)

router = APIRouter(prefix="/compliance", tags=["compliance"])

# SLA days per regulation
_DSAR_SLA: dict[Regulation, int] = {
    Regulation.GDPR: 30,
    Regulation.CCPA: 45,
    Regulation.HIPAA: 30,
}


@router.post("/consent", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED)
async def record_consent(
    payload: ConsentCreate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> ConsentRecord:
    # M-6 compliance fix: enforce the current user's agency_id to prevent cross-tenant operations
    agency_id = current_user.agency_id
    subject_hash = hash_identifier(str(payload.subject_email), str(agency_id))

    # Upsert: one record per (agency, subject_hash, purpose)
    existing = await db.execute(
        select(ConsentRecord).where(
            ConsentRecord.agency_id == agency_id,
            ConsentRecord.subject_hash == subject_hash,
            ConsentRecord.purpose == payload.purpose,
        )
    )
    record = existing.scalar_one_or_none()

    if record:
        record.granted = payload.granted
        record.do_not_sell = payload.do_not_sell
        record.withdrawn_at = None if payload.granted else datetime.now(timezone.utc)
        record.granted_at = datetime.now(timezone.utc) if payload.granted else record.granted_at
    else:
        record = ConsentRecord(
            agency_id=agency_id,
            client_id=payload.client_id,
            subject_hash=subject_hash,
            purpose=payload.purpose,
            granted=payload.granted,
            do_not_sell=payload.do_not_sell,
            consent_text=payload.consent_text or "",
            consent_version=payload.consent_version or "v1.0",
            ip_address=_truncate_ip(payload.ip_address),  # M-04: truncate IP to /24
            source=payload.source,
            granted_at=datetime.now(timezone.utc),
        )
        db.add(record)

    await db.commit()
    await db.refresh(record)
    return record


@router.post("/consent/withdraw", response_model=ConsentResponse)
async def withdraw_consent(
    payload: ConsentWithdraw,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> ConsentRecord:
    # H-01: enforce the current user's agency_id to prevent cross-tenant operations
    withdraw_agency_id = current_user.agency_id
    subject_hash = hash_identifier(str(payload.subject_email), str(withdraw_agency_id))
    result = await db.execute(
        select(ConsentRecord).where(
            ConsentRecord.agency_id == withdraw_agency_id,
            ConsentRecord.subject_hash == subject_hash,
            ConsentRecord.purpose == payload.purpose,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Consent record not found")

    record.granted = False
    record.withdrawn_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/consent/{subject_hash}", response_model=list[ConsentResponse])
async def get_consent_by_hash(
    subject_hash: str,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> list[ConsentRecord]:
    result = await db.execute(
        select(ConsentRecord).where(
            ConsentRecord.agency_id == current_user.agency_id,
            ConsentRecord.subject_hash == subject_hash,
        )
    )
    return list(result.scalars().all())


@router.post("/dsar", response_model=DSARResponse, status_code=status.HTTP_201_CREATED)
async def submit_dsar(
    payload: DSARCreate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> DSARRequest:
    sla_days = _DSAR_SLA.get(payload.regulation, 30)
    due_date = datetime.now(timezone.utc) + timedelta(days=sla_days)

    # M-6 + C-3 compliance fix: enforce current_user.agency_id + hash and store subject_email
    dsar_agency_id = current_user.agency_id
    from app.core.compliance.anonymizer import hash_identifier
    hashed_email = hash_identifier(str(payload.subject_email), str(dsar_agency_id))

    dsar = DSARRequest(
        agency_id=dsar_agency_id,
        request_type=payload.request_type,
        regulation=payload.regulation,
        subject_email_hash=hashed_email,
        subject_name=None,  # C-3: do not store plaintext name (data minimization principle)
        status=DSARStatus.PENDING,
        due_date=due_date,
    )
    db.add(dsar)
    # H-7: audit log
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="dsar.submit",
        actor=current_user,
        agency_id=current_user.agency_id,
        resource=str(dsar.id,
    ) if dsar.id else "")
    await db.commit()
    await db.refresh(dsar)
    return dsar


@router.get("/dsar", response_model=list[DSARResponse])
async def list_dsar(
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> list[DSARRequest]:
    result = await db.execute(
        select(DSARRequest)
        .where(DSARRequest.agency_id == current_user.agency_id)
        .order_by(DSARRequest.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/dsar/{dsar_id}", response_model=DSARResponse)
async def get_dsar(
    dsar_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> DSARRequest:
    result = await db.execute(
        select(DSARRequest).where(
            DSARRequest.id == dsar_id,
            DSARRequest.agency_id == current_user.agency_id,
        )
    )
    dsar = result.scalar_one_or_none()
    if not dsar:
        raise HTTPException(status_code=404, detail="DSAR request not found")
    return dsar


@router.patch("/dsar/{dsar_id}", response_model=DSARResponse)
async def update_dsar_status(
    dsar_id: uuid.UUID,
    payload: DSARUpdateStatus,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> DSARRequest:
    result = await db.execute(
        select(DSARRequest).where(
            DSARRequest.id == dsar_id,
            DSARRequest.agency_id == current_user.agency_id,
        )
    )
    dsar = result.scalar_one_or_none()
    if not dsar:
        raise HTTPException(status_code=404, detail="DSAR request not found")

    dsar.status = payload.status
    if payload.notes:
        dsar.notes = payload.notes
    if payload.rejection_reason:
        dsar.rejection_reason = payload.rejection_reason
    if payload.status == DSARStatus.COMPLETED:
        dsar.completed_at = datetime.now(timezone.utc)

    # H-08: DSAR status changes must be audited
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event=f"dsar.{payload.status.value}",
        actor=current_user,
        agency_id=current_user.agency_id,
        resource=str(dsar_id,
    ))
    await db.commit()
    await db.refresh(dsar)
    return dsar
