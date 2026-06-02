"""Team management: invitations and member CRUD.

All endpoints are scoped to the calling user's agency. State-changing routes
write to the audit log. Email and full_name are stored Fernet-encrypted; the
invitation token itself is only ever returned in the response and stored as
a SHA-256 hash.
"""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit_event
from app.core.config import settings
from app.core.database import get_platform_db
from app.core.deps import get_current_user
from app.core.permissions import require_permission
from app.core.pii_crypto import decrypt_pii, encrypt_pii, hash_email
from app.models.invitation import UserInvitation
from app.models.user import User, UserRole

router = APIRouter(prefix="/team", tags=["team"])

INVITE_EXPIRY_DAYS = 7


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


# ── Schemas ────────────────────────────────────────────────────────────────


class InvitationCreateRequest(BaseModel):
    email: EmailStr
    # PR 4: free-form role code (must exist in `roles` table; FK enforces).
    role: str
    client_id: Optional[uuid.UUID] = None


class InvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    role: str
    client_id: Optional[uuid.UUID]
    invited_by: uuid.UUID
    expires_at: datetime
    accepted_at: Optional[datetime]
    revoked_at: Optional[datetime]
    created_at: datetime


class InvitationCreateResponse(InvitationResponse):
    invite_url: str
    raw_token: str


class MemberResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    client_id: Optional[uuid.UUID]
    is_active: bool
    last_login_at: Optional[datetime]


class MemberUpdateRequest(BaseModel):
    role: Optional[str] = None
    client_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


# ── Helpers ────────────────────────────────────────────────────────────────


def _invitation_to_response(inv: UserInvitation) -> InvitationResponse:
    return InvitationResponse(
        id=inv.id,
        email=decrypt_pii(inv.email_encrypted),
        role=str(inv.role),
        client_id=inv.client_id,
        invited_by=inv.invited_by,
        expires_at=inv.expires_at,
        accepted_at=inv.accepted_at,
        revoked_at=inv.revoked_at,
        created_at=inv.created_at,
    )


def _member_to_response(user: User) -> MemberResponse:
    return MemberResponse(
        id=user.id,
        email=decrypt_pii(user.email),
        full_name=decrypt_pii(user.full_name),
        role=str(user.role),
        client_id=user.client_id,
        is_active=user.is_active,
        last_login_at=user.last_login_at,
    )


# ── Invitations ────────────────────────────────────────────────────────────


@router.post(
    "/invitations",
    response_model=InvitationCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(
    payload: InvitationCreateRequest,
    db: AsyncSession = Depends(get_platform_db),
    admin: User = Depends(require_permission("team.invite")),
) -> InvitationCreateResponse:
    email_hash = hash_email(payload.email)

    # Reject if a user with this email already exists in the agency.
    existing_user = await db.execute(
        select(User).where(
            User.agency_id == admin.agency_id,
            User.email_hash == email_hash,
        )
    )
    if existing_user.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists in this agency",
        )

    now = datetime.now(timezone.utc)
    existing_inv = await db.execute(
        select(UserInvitation).where(
            UserInvitation.agency_id == admin.agency_id,
            UserInvitation.email_hash == email_hash,
            UserInvitation.accepted_at.is_(None),
            UserInvitation.revoked_at.is_(None),
            UserInvitation.expires_at > now,
        )
    )
    if existing_inv.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A pending invitation for this email already exists",
        )

    raw_token = secrets.token_urlsafe(32)
    invitation = UserInvitation(
        agency_id=admin.agency_id,
        client_id=payload.client_id,
        email_hash=email_hash,
        email_encrypted=encrypt_pii(payload.email),
        role=payload.role,
        token_hash=_hash_token(raw_token),
        invited_by=admin.id,
        expires_at=now + timedelta(days=INVITE_EXPIRY_DAYS),
    )
    db.add(invitation)
    await db.flush()
    await audit_event(
        db=db,
        event="team.invitation.create",
        actor=admin,
        agency_id=admin.agency_id,
        resource=str(invitation.id),
        after={"role": str(payload.role)},
    )
    await db.commit()
    await db.refresh(invitation)

    invite_url = f"{settings.frontend_base_url}/accept-invite?token={raw_token}"
    base = _invitation_to_response(invitation)
    return InvitationCreateResponse(
        **base.model_dump(),
        invite_url=invite_url,
        raw_token=raw_token,
    )


@router.get("/invitations", response_model=list[InvitationResponse])
async def list_invitations(
    db: AsyncSession = Depends(get_platform_db),
    admin: User = Depends(require_permission("team.view")),
) -> list[InvitationResponse]:
    result = await db.execute(
        select(UserInvitation)
        .where(UserInvitation.agency_id == admin.agency_id)
        .order_by(UserInvitation.created_at.desc())
    )
    return [_invitation_to_response(inv) for inv in result.scalars().all()]


@router.delete("/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invitation(
    invitation_id: uuid.UUID,
    db: AsyncSession = Depends(get_platform_db),
    admin: User = Depends(require_permission("team.invite")),
) -> None:
    result = await db.execute(
        select(UserInvitation).where(
            UserInvitation.id == invitation_id,
            UserInvitation.agency_id == admin.agency_id,
        )
    )
    inv = result.scalar_one_or_none()
    if inv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )
    if inv.accepted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation already accepted",
        )
    if inv.revoked_at is None:
        inv.revoked_at = datetime.now(timezone.utc)
    await audit_event(
        db=db,
        event="team.invitation.revoke",
        actor=admin,
        agency_id=admin.agency_id,
        resource=str(inv.id),
        before={"revoked_at": None},
        after={"revoked_at": inv.revoked_at.isoformat() if inv.revoked_at else None},
    )
    await db.commit()


# ── Members ────────────────────────────────────────────────────────────────


@router.get("/members", response_model=list[MemberResponse])
async def list_members(
    db: AsyncSession = Depends(get_platform_db),
    current_user: User = Depends(get_current_user),
) -> list[MemberResponse]:
    result = await db.execute(
        select(User)
        .where(User.agency_id == current_user.agency_id)
        .order_by(User.created_at.desc())
    )
    return [_member_to_response(u) for u in result.scalars().all()]


@router.patch("/members/{user_id}", response_model=MemberResponse)
async def update_member(
    user_id: uuid.UUID,
    payload: MemberUpdateRequest,
    db: AsyncSession = Depends(get_platform_db),
    admin: User = Depends(require_permission("team.role.update")),
) -> MemberResponse:
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.agency_id == admin.agency_id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    # If demoting an admin (or deactivating), ensure at least one active admin remains.
    will_lose_admin = (
        member.role == "agency_admin"
        and (
            (payload.role is not None and payload.role != "agency_admin")
            or (payload.is_active is False)
        )
    )
    if will_lose_admin:
        admin_count = await db.execute(
            select(User).where(
                User.agency_id == admin.agency_id,
                User.role == "agency_admin",
                User.is_active.is_(True),
            )
        )
        active_admins = admin_count.scalars().all()
        if len(active_admins) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote or deactivate the last active agency admin",
            )

    before_snapshot = {
        "role": str(member.role),
        "client_id": str(member.client_id) if member.client_id else None,
        "is_active": member.is_active,
    }
    if payload.role is not None:
        member.role = payload.role
    if payload.client_id is not None:
        member.client_id = payload.client_id
    if payload.is_active is not None:
        member.is_active = payload.is_active
    after_snapshot = {
        "role": str(member.role),
        "client_id": str(member.client_id) if member.client_id else None,
        "is_active": member.is_active,
    }

    await audit_event(
        db=db,
        event="team.member.update",
        actor=admin,
        agency_id=admin.agency_id,
        resource=str(member.id),
        before=before_snapshot,
        after=after_snapshot,
    )
    await db.commit()
    await db.refresh(member)
    return _member_to_response(member)
