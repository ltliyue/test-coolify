from __future__ import annotations
from typing import Optional
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.role_codes import BUILTIN_ROLES, UserRole, PLATFORM_ROLES  # re-export for callers

__all__ = ["User", "UserRole", "PLATFORM_ROLES", "BUILTIN_ROLES"]


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Nullable: platform-tier users (platform_super_admin / platform_admin)
    # do not belong to any agency.
    agency_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agencies.id", ondelete="CASCADE"),
        nullable=True,
    )
    client_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="SET NULL"),
        nullable=True,
    )
    # M-02/M-03: email and full_name store Fernet-encrypted values; email_hash is used for lookup
    email: Mapped[str] = mapped_column(String, nullable=False)  # Stores encrypted value (or legacy plaintext for compatibility)
    email_hash: Mapped[str] = mapped_column(String, nullable=False, index=True)  # SHA-256, used in WHERE lookups
    hashed_password: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    google_id: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)  # Stores encrypted value (or legacy plaintext for compatibility)
    # PR 4: role is a free-form code referencing the `roles` table. The
    # Python `UserRole` constants in app.core.role_codes are convenience
    # values for built-ins; custom roles use raw strings.
    role: Mapped[str] = mapped_column(
        String,
        ForeignKey("roles.code", ondelete="RESTRICT"),
        nullable=False,
        default="agency_ops",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
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
