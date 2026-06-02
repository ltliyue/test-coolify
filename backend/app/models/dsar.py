from __future__ import annotations
from typing import Optional
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import DSARStatus, DSARType, Regulation


class DSARRequest(Base):
    __tablename__ = "dsar_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agencies.id", ondelete="CASCADE"),
        nullable=False,
    )
    request_type: Mapped[DSARType] = mapped_column(
        SAEnum(DSARType, name="dsar_type", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    regulation: Mapped[Regulation] = mapped_column(
        SAEnum(Regulation, name="regulation", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    # C-03: column renamed to subject_email_hash (stores the hash, not plaintext)
    subject_email_hash: Mapped[str] = mapped_column("subject_email_hash", String, nullable=False)
    subject_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Already nulled at the API layer (not stored)
    verification_token: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[DSARStatus] = mapped_column(
        SAEnum(DSARStatus, name="dsar_status", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=DSARStatus.PENDING,
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    extended_due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    response_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
