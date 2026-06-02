from __future__ import annotations
from typing import Optional
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.encrypted_types import EncryptedDSN


class AgencyStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"
    trial = "trial"


class AgencyPlan(str, enum.Enum):
    starter = "starter"
    growth = "growth"
    enterprise = "enterprise"


class Agency(Base):
    __tablename__ = "agencies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    status: Mapped[AgencyStatus] = mapped_column(
        Enum(AgencyStatus, name="agency_status"),
        nullable=False,
        default=AgencyStatus.trial,
    )
    plan: Mapped[AgencyPlan] = mapped_column(
        Enum(AgencyPlan, name="agency_plan"),
        nullable=False,
        default=AgencyPlan.starter,
    )
    brand_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    monthly_token_budget: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1000000
    )
    is_suspended: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    suspended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    suspended_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Per-Agency database isolation (see docs/MULTI-TENANT-DB.md).
    # db_schema: Postgres schema holding this agency's row-isolated data.
    # db_dsn: forward-compat — when set, future TenantSessionRouter routes
    # queries to this DSN instead of the shared cluster.
    # Legacy from PR 1: kept for backward-compat with the migration script
    # only. PR 2 moves every Agency onto its own physical DB; db_dsn is the
    # new source of truth and queries route through TenantSessionRouter.
    db_schema: Mapped[str] = mapped_column(String, nullable=False)
    # Encrypted at rest via EncryptedDSN TypeDecorator. NULL is only valid
    # during the brief PR-2 migration window — after migration 024,
    # Postgres enforces NOT NULL.
    db_dsn: Mapped[Optional[str]] = mapped_column(EncryptedDSN, nullable=True)
    # Previous DSN preserved during rotation/migration for rollback.
    db_dsn_previous: Mapped[Optional[str]] = mapped_column(
        EncryptedDSN, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
