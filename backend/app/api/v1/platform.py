"""Platform-tier admin endpoints.

These endpoints are reserved for the ReceptivIQ ops team (roles
``platform_super_admin`` / ``platform_admin``). They operate across all
Agencies and are NOT scoped by ``agency_id`` on the calling user.

All state-changing routes write an audit log entry. Audit rows produced
by platform users carry ``agency_id=NULL`` (the column is nullable in the
audit_log schema) and the target agency id in ``resource_id``.
"""
from __future__ import annotations

import hashlib
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit_event
from app.core.config import settings
from app.core.database import get_platform_db
from app.core.permissions import require_permission
from app.core.pii_crypto import decrypt_pii, encrypt_pii, hash_email
from app.models.agency import Agency, AgencyPlan
from app.models.client import Client
from app.models.invitation import UserInvitation
from app.models.user import PLATFORM_ROLES, User, UserRole

router = APIRouter(prefix="/platform", tags=["platform"])

INVITE_EXPIRY_DAYS = 7


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")
    return slug or "agency"


# ── Schemas ────────────────────────────────────────────────────────────────


class AgencyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    plan: Optional[AgencyPlan] = None


class AgencyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    plan: str
    monthly_token_budget: int
    is_suspended: bool
    suspended_at: Optional[datetime]
    suspended_reason: Optional[str]
    created_at: datetime
    member_count: int = 0
    client_count: int = 0


class AgencySuspendRequest(BaseModel):
    reason: Optional[str] = None


class InviteAdminRequest(BaseModel):
    email: EmailStr


class InviteAdminResponse(BaseModel):
    invite_url: str
    raw_token: str
    expires_at: datetime


class PlatformUserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    last_login_at: Optional[datetime]
    created_at: datetime


class PlatformInviteRequest(BaseModel):
    email: EmailStr
    role: str

    def normalized_role(self) -> str:
        if self.role not in PLATFORM_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role must be one of platform_admin / platform_super_admin",
            )
        return self.role


class PlatformInviteResponse(BaseModel):
    invite_url: str
    raw_token: str
    expires_at: datetime
    role: str


# ── Helpers ────────────────────────────────────────────────────────────────


async def _agency_to_response(db: AsyncSession, agency: Agency) -> AgencyResponse:
    member_count_q = await db.execute(
        select(func.count(User.id)).where(User.agency_id == agency.id)
    )
    client_count_q = await db.execute(
        select(func.count(Client.id)).where(Client.agency_id == agency.id)
    )
    return AgencyResponse(
        id=agency.id,
        name=agency.name,
        slug=agency.slug,
        plan=agency.plan.value if hasattr(agency.plan, "value") else str(agency.plan),
        monthly_token_budget=agency.monthly_token_budget,
        is_suspended=agency.is_suspended,
        suspended_at=agency.suspended_at,
        suspended_reason=agency.suspended_reason,
        created_at=agency.created_at,
        member_count=int(member_count_q.scalar_one() or 0),
        client_count=int(client_count_q.scalar_one() or 0),
    )


async def _platform_audit(
    db: AsyncSession,
    user: User,
    action: str,
    resource_type: str,
    resource_id: str = "",
    before: Optional[dict] = None,
    after: Optional[dict] = None,
) -> None:
    """Thin shim that forwards platform events through the unified
    :func:`audit_event` entry point. ``agency_id`` is permitted to be
    None for platform-tier actors (the audit_logs column is nullable).
    Audit failures propagate as :class:`AuditWriteError` and surface as
    5xx.
    """
    await audit_event(
        db=db,
        event=action,
        actor=user,
        agency_id=user.agency_id,
        resource=resource_id,
        before=before,
        after=after,
    )


# ── Agencies ───────────────────────────────────────────────────────────────


@router.get("/agencies", response_model=list[AgencyResponse])
async def list_agencies(
    db: AsyncSession = Depends(get_platform_db),
    _admin: User = Depends(require_permission("platform.agency.view")),
) -> list[AgencyResponse]:
    result = await db.execute(select(Agency).order_by(Agency.created_at.desc()))
    agencies = result.scalars().all()
    return [await _agency_to_response(db, a) for a in agencies]


@router.post(
    "/agencies",
    response_model=AgencyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_agency(
    payload: AgencyCreateRequest,
    db: AsyncSession = Depends(get_platform_db),
    admin: User = Depends(require_permission("platform.agency.create")),
) -> AgencyResponse:
    base_slug = _slugify(payload.name)
    slug = base_slug
    counter = 1
    while True:
        found = await db.execute(select(Agency).where(Agency.slug == slug))
        if found.scalar_one_or_none() is None:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    from app.core.tenant_provisioner import provision_tenant_database

    # db_schema kept for legacy NOT NULL constraint; PR 2 routes via db_dsn.
    schema_name = "tenant_" + slug.replace("-", "_")
    agency = Agency(name=payload.name, slug=slug, db_schema=schema_name)
    if payload.plan is not None:
        agency.plan = payload.plan
    db.add(agency)
    await db.flush()
    # Provision a dedicated per-Agency database and persist its encrypted DSN.
    agency.db_dsn = await provision_tenant_database(agency=agency, platform_db=db)
    await _platform_audit(
        db, admin, action="platform.agency.create",
        resource_type="agency", resource_id=str(agency.id),
    )
    await db.commit()
    await db.refresh(agency)
    return await _agency_to_response(db, agency)


@router.get("/agencies/{agency_id}", response_model=AgencyResponse)
async def get_agency(
    agency_id: uuid.UUID,
    db: AsyncSession = Depends(get_platform_db),
    _admin: User = Depends(require_permission("platform.agency.view")),
) -> AgencyResponse:
    result = await db.execute(select(Agency).where(Agency.id == agency_id))
    agency = result.scalar_one_or_none()
    if agency is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agency not found")
    return await _agency_to_response(db, agency)


@router.post("/agencies/{agency_id}/suspend", response_model=AgencyResponse)
async def suspend_agency(
    agency_id: uuid.UUID,
    payload: AgencySuspendRequest,
    db: AsyncSession = Depends(get_platform_db),
    admin: User = Depends(require_permission("platform.agency.suspend")),
) -> AgencyResponse:
    result = await db.execute(select(Agency).where(Agency.id == agency_id))
    agency = result.scalar_one_or_none()
    if agency is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agency not found")
    agency.is_suspended = True
    agency.suspended_at = datetime.now(timezone.utc)
    agency.suspended_reason = payload.reason
    await _platform_audit(
        db, admin, action="platform.agency.suspend",
        resource_type="agency", resource_id=str(agency.id),
    )
    await db.commit()
    await db.refresh(agency)
    return await _agency_to_response(db, agency)


@router.post("/agencies/{agency_id}/unsuspend", response_model=AgencyResponse)
async def unsuspend_agency(
    agency_id: uuid.UUID,
    db: AsyncSession = Depends(get_platform_db),
    admin: User = Depends(require_permission("platform.agency.suspend")),
) -> AgencyResponse:
    result = await db.execute(select(Agency).where(Agency.id == agency_id))
    agency = result.scalar_one_or_none()
    if agency is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agency not found")
    agency.is_suspended = False
    agency.suspended_at = None
    agency.suspended_reason = None
    await _platform_audit(
        db, admin, action="platform.agency.unsuspend",
        resource_type="agency", resource_id=str(agency.id),
    )
    await db.commit()
    await db.refresh(agency)
    return await _agency_to_response(db, agency)


@router.post(
    "/agencies/{agency_id}/invite-admin",
    response_model=InviteAdminResponse,
    status_code=status.HTTP_201_CREATED,
)
async def invite_agency_admin(
    agency_id: uuid.UUID,
    payload: InviteAdminRequest,
    db: AsyncSession = Depends(get_platform_db),
    admin: User = Depends(require_permission("platform.agency.invite_admin")),
) -> InviteAdminResponse:
    result = await db.execute(select(Agency).where(Agency.id == agency_id))
    agency = result.scalar_one_or_none()
    if agency is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agency not found")

    email_hash = hash_email(payload.email)
    existing_user = await db.execute(
        select(User).where(
            User.agency_id == agency.id,
            User.email_hash == email_hash,
        )
    )
    if existing_user.scalar_one_or_none() is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "A user with this email already exists in this agency",
        )

    now = datetime.now(timezone.utc)
    existing_inv = await db.execute(
        select(UserInvitation).where(
            UserInvitation.agency_id == agency.id,
            UserInvitation.email_hash == email_hash,
            UserInvitation.accepted_at.is_(None),
            UserInvitation.revoked_at.is_(None),
            UserInvitation.expires_at > now,
        )
    )
    if existing_inv.scalar_one_or_none() is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "A pending invitation for this email already exists",
        )

    raw_token = secrets.token_urlsafe(32)
    invitation = UserInvitation(
        agency_id=agency.id,
        client_id=None,
        email_hash=email_hash,
        email_encrypted=encrypt_pii(payload.email),
        role=UserRole.agency_admin,
        token_hash=_hash_token(raw_token),
        invited_by=admin.id,
        expires_at=now + timedelta(days=INVITE_EXPIRY_DAYS),
    )
    db.add(invitation)
    await db.flush()
    await _platform_audit(
        db, admin, action="platform.agency.invite_admin",
        resource_type="user_invitation", resource_id=str(invitation.id),
    )
    await db.commit()
    await db.refresh(invitation)

    invite_url = f"{settings.frontend_base_url}/accept-invite?token={raw_token}"
    return InviteAdminResponse(
        invite_url=invite_url,
        raw_token=raw_token,
        expires_at=invitation.expires_at,
    )


# ── Platform users ─────────────────────────────────────────────────────────


@router.get("/users", response_model=list[PlatformUserResponse])
async def list_platform_users(
    db: AsyncSession = Depends(get_platform_db),
    _admin: User = Depends(require_permission("platform.users.view")),
) -> list[PlatformUserResponse]:
    result = await db.execute(
        select(User)
        .where(User.role.in_(list(PLATFORM_ROLES)))
        .order_by(User.created_at.desc())
    )
    rows = result.scalars().all()
    return [
        PlatformUserResponse(
            id=u.id,
            email=decrypt_pii(u.email),
            full_name=decrypt_pii(u.full_name),
            role=str(u.role),
            is_active=u.is_active,
            last_login_at=u.last_login_at,
            created_at=u.created_at,
        )
        for u in rows
    ]


@router.post(
    "/users/invitations",
    response_model=PlatformInviteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def invite_platform_user(
    payload: PlatformInviteRequest,
    db: AsyncSession = Depends(get_platform_db),
    admin: User = Depends(require_permission("platform.users.invite")),
) -> PlatformInviteResponse:
    role = payload.normalized_role()
    email_hash = hash_email(payload.email)

    existing_user = await db.execute(
        select(User).where(User.email_hash == email_hash)
    )
    if existing_user.scalar_one_or_none() is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "A user with this email already exists",
        )

    now = datetime.now(timezone.utc)
    existing_inv = await db.execute(
        select(UserInvitation).where(
            UserInvitation.agency_id.is_(None),
            UserInvitation.email_hash == email_hash,
            UserInvitation.accepted_at.is_(None),
            UserInvitation.revoked_at.is_(None),
            UserInvitation.expires_at > now,
        )
    )
    if existing_inv.scalar_one_or_none() is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "A pending platform invitation for this email already exists",
        )

    raw_token = secrets.token_urlsafe(32)
    invitation = UserInvitation(
        agency_id=None,
        client_id=None,
        email_hash=email_hash,
        email_encrypted=encrypt_pii(payload.email),
        role=str(role),
        token_hash=_hash_token(raw_token),
        invited_by=admin.id,
        expires_at=now + timedelta(days=INVITE_EXPIRY_DAYS),
    )
    db.add(invitation)
    await db.flush()
    await _platform_audit(
        db, admin, action="platform.user.invite",
        resource_type="user_invitation", resource_id=str(invitation.id),
    )
    await db.commit()
    await db.refresh(invitation)

    invite_url = f"{settings.frontend_base_url}/accept-invite?token={raw_token}"
    return PlatformInviteResponse(
        invite_url=invite_url,
        raw_token=raw_token,
        expires_at=invitation.expires_at,
        role=str(role),
    )
