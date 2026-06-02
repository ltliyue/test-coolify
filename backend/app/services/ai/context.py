from __future__ import annotations
"""
Shared Context assembler.
Provides brand config, historical campaign summary, Agency quota limits, and other context to the AI Agent.
"""
from typing import Optional, Any, Dict
from dataclasses import dataclass, field
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class SharedContext:
    agency_id: str
    client_id: Optional[str]
    # Brand info (read from Agency.brand_config)
    brand_name: Optional[str] = None
    brand_voice: Optional[str] = None
    industry: Optional[str] = None
    target_audience: Optional[str] = None
    # Token budget
    monthly_token_budget: int = 1_000_000
    tokens_used_this_month: int = 0
    budget_remaining: int = 1_000_000
    # Additional context (for agent use)
    extra: Dict[str, Any] = field(default_factory=dict)


async def build_shared_context(
    db: AsyncSession,
    agency_id: uuid.UUID,
    client_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> SharedContext:
    """
    Build the Agency's shared context:
    1. Read basic info and monthly_token_budget from Agency
    2. Aggregate current-month usage from the token_usage table
    3. Assemble the SharedContext
    """
    from app.models.agency import Agency
    from app.models.token_usage import TokenUsage

    # 1. Agency basic info
    agency = await db.get(Agency, agency_id)
    brand_config: Dict[str, Any] = {}
    monthly_budget = 1_000_000
    if agency is not None:
        brand_config = agency.brand_config or {}
        monthly_budget = agency.monthly_token_budget

    # 2. current month token usage
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.coalesce(func.sum(TokenUsage.total_tokens), 0))
        .where(TokenUsage.agency_id == agency_id)
        .where(TokenUsage.created_at >= month_start)
    )
    tokens_used = int(result.scalar() or 0)

    return SharedContext(
        agency_id=str(agency_id),
        client_id=str(client_id) if client_id else None,
        brand_name=brand_config.get("name"),
        brand_voice=brand_config.get("brand_voice"),
        industry=brand_config.get("industry"),
        target_audience=brand_config.get("target_audience"),
        monthly_token_budget=monthly_budget,
        tokens_used_this_month=tokens_used,
        budget_remaining=max(0, monthly_budget - tokens_used),
        extra=extra or {},
    )
