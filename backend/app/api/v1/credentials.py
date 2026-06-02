from __future__ import annotations
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_db import get_tenant_db
from app.core.deps import get_current_user
from app.core.permissions import require_permission
from app.core.encryption import encrypt_credentials
from app.models.credential import Credential
from app.models.enums import CredentialStatus
from app.models.user import User
from app.schemas.credential import CredentialCreate, CredentialResponse

router = APIRouter(prefix="/credentials", tags=["credentials"])


@router.post("/", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def store_credential(
    payload: CredentialCreate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(require_permission("integrations.connect")),
) -> CredentialResponse:
    encrypted = encrypt_credentials(payload.data)
    cred = Credential(
        agency_id=current_user.agency_id,
        client_id=None,
        platform=payload.platform,
        credential_type=payload.credential_type,
        encrypted_data=encrypted,
        scopes=payload.scopes,
        created_by=current_user.id,
    )
    db.add(cred)
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="credential.store",
        actor=current_user,
        agency_id=current_user.agency_id,
        resource=payload.platform,
    )
    await db.commit()
    await db.refresh(cred)
    return CredentialResponse.model_validate(cred)


@router.get("/", response_model=list[CredentialResponse])
async def list_credentials(
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> list[CredentialResponse]:
    result = await db.execute(
        select(Credential).where(Credential.agency_id == current_user.agency_id)
    )
    credentials = result.scalars().all()
    return [CredentialResponse.model_validate(c) for c in credentials]


@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_credential(
    credential_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(require_permission("integrations.disconnect")),
) -> None:
    result = await db.execute(
        select(Credential).where(
            Credential.id == credential_id,
            Credential.agency_id == current_user.agency_id,
        )
    )
    cred = result.scalar_one_or_none()
    if not cred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found",
        )
    cred.status = CredentialStatus.REVOKED
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="credential.revoke",
        actor=current_user,
        agency_id=current_user.agency_id,
        resource=str(credential_id,
    ))
    await db.commit()
