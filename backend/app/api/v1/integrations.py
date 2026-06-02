from __future__ import annotations
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_db import get_tenant_db
from app.core.deps import get_current_user
from app.core.encryption import encrypt_credentials
from app.models.credential import Credential
from app.models.enums import AuthType, CredentialType, IntegrationPlatform, IntegrationStatus
from app.models.integration import Integration
from app.models.sync_log import SyncLog
from app.models.user import User
from app.schemas.integration import (
    ConnectRequest,
    IntegrationListItem,
    IntegrationResponse,
    PlatformInfo,
    SyncLogResponse,
)
from app.services.platform_registry import get_platform_info, list_platforms

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/platforms", response_model=list[PlatformInfo])
async def list_all_platforms(current_user: User = Depends(get_current_user)) -> list[dict]:
    return list_platforms()


@router.get("/", response_model=list[IntegrationListItem])
async def list_integrations(
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> list[Integration]:
    result = await db.execute(
        select(Integration).where(Integration.agency_id == current_user.agency_id)
    )
    return list(result.scalars().all())


@router.post("/connect", response_model=IntegrationResponse, status_code=status.HTTP_201_CREATED)
async def connect_platform(
    payload: ConnectRequest,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> Integration:
    """Connect a platform using API key or OAuth credentials."""
    platform_key = payload.platform.value
    platform_info = get_platform_info(platform_key)
    if not platform_info:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform_key}")

    auth_type_str = platform_info["auth_type"]
    if auth_type_str == AuthType.OAUTH:
        raise HTTPException(
            status_code=400,
            detail="OAuth platforms must be connected via the OAuth flow endpoint",
        )

    # Validate required fields
    required_keys = [f["key"] for f in platform_info.get("connect_fields", []) if f["required"]]
    missing = [k for k in required_keys if k not in payload.data]
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing required fields: {missing}")

    # Encrypt and store credentials
    encrypted = encrypt_credentials(payload.data)
    cred = Credential(
        agency_id=current_user.agency_id,
        platform=platform_key,
        credential_type=CredentialType.API_KEY,
        encrypted_data=encrypted,
        created_by=current_user.id,
    )
    db.add(cred)
    await db.flush()

    # Upsert integration record
    existing = await db.execute(
        select(Integration).where(
            Integration.agency_id == current_user.agency_id,
            Integration.platform == IntegrationPlatform(platform_key),
        )
    )
    integration = existing.scalar_one_or_none()

    if integration:
        integration.credential_id = cred.id
        integration.status = IntegrationStatus.CONNECTED
        integration.connected_at = datetime.now(timezone.utc)
        integration.error_message = None
    else:
        integration = Integration(
            agency_id=current_user.agency_id,
            platform=IntegrationPlatform(platform_key),
            auth_type=AuthType.API_KEY,
            status=IntegrationStatus.CONNECTED,
            credential_id=cred.id,
            connected_at=datetime.now(timezone.utc),
            created_by=current_user.id,
        )
        db.add(integration)

    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="integration.connect",
        actor=current_user,
        agency_id=current_user.agency_id,
        resource=platform_key,
    )
    await db.commit()
    await db.refresh(integration)
    return integration


@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(
    integration_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> Integration:
    result = await db.execute(
        select(Integration).where(
            Integration.id == integration_id,
            Integration.agency_id == current_user.agency_id,
        )
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return integration


@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_integration(
    integration_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> None:
    result = await db.execute(
        select(Integration).where(
            Integration.id == integration_id,
            Integration.agency_id == current_user.agency_id,
        )
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    integration.status = IntegrationStatus.DISCONNECTED
    integration.connected_at = None
    integration.credential_id = None
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="integration.disconnect",
        actor=current_user,
        agency_id=current_user.agency_id,
        resource=str(integration_id,
    ))
    await db.commit()


@router.get("/{integration_id}/sync-logs", response_model=list[SyncLogResponse])
async def list_sync_logs(
    integration_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> list[SyncLog]:
    # Verify ownership
    result = await db.execute(
        select(Integration).where(
            Integration.id == integration_id,
            Integration.agency_id == current_user.agency_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Integration not found")

    logs = await db.execute(
        select(SyncLog)
        .where(SyncLog.integration_id == integration_id)
        .order_by(SyncLog.started_at.desc())
        .limit(50)
    )
    return list(logs.scalars().all())


@router.post("/{integration_id}/sync", status_code=status.HTTP_202_ACCEPTED)
async def trigger_sync(
    integration_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Manually trigger a sync. Creates a sync_log record and dispatches Celery task."""
    result = await db.execute(
        select(Integration).where(
            Integration.id == integration_id,
            Integration.agency_id == current_user.agency_id,
        )
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    if integration.status != IntegrationStatus.CONNECTED:
        raise HTTPException(status_code=400, detail="Integration is not connected")

    from app.models.enums import SyncStatus
    log = SyncLog(
        integration_id=integration_id,
        agency_id=current_user.agency_id,
        triggered_by="manual",
        status=SyncStatus.PENDING,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)

    # dispatch Celery ETL synctask
    try:
        from app.tasks.etl_tasks import run_etl_sync
        from datetime import datetime, timedelta, timezone
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        run_etl_sync.delay(str(integration.id), today, today)
    except Exception as _celery_err:
        import logging
        logging.getLogger(__name__).warning("Celery task dispatch failed: %s", _celery_err)
    return {"sync_log_id": str(log.id), "status": "pending"}
