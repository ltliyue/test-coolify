from __future__ import annotations
"""Campaign Budget Config ORM — budget configs & alerting rules."""
import uuid
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CampaignBudgetConfig(Base):
    __tablename__ = "campaign_budget_configs"
    __table_args__ = (
        UniqueConstraint("agency_id", "platform", "external_campaign_id", name="uq_budget_config"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    client_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    external_campaign_id: Mapped[str] = mapped_column(String(255), nullable=False)
    campaign_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    daily_budget: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    total_budget: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    pacing_alert_threshold: Mapped[float] = mapped_column(Float, default=0.15, nullable=False)
    alert_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
