from __future__ import annotations
"""AI Brain API route。"""
import uuid
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_platform_db
from app.core.tenant_db import get_tenant_db
from app.core.deps import get_current_user
from app.core.monitoring import get_langfuse
from app.models.user import User
from app.models.token_usage import TokenUsage
from app.models.agency import Agency
from app.schemas.ai import AIRequest, AIResponse, MonthlyUsageSummary
from app.services.ai.context import build_shared_context

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=AIResponse)
async def ai_chat(
    payload: AIRequest,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> AIResponse:
    """
    Send a request to the AI Brain.
    Auto-checks token budget, records usage, and traces the LLM call via Langfuse.
    """
    agency_id: uuid.UUID = current_user.agency_id
    client_id: Optional[uuid.UUID] = (
        uuid.UUID(payload.client_id) if payload.client_id else None
    )

    # Build context
    ctx = await build_shared_context(db, agency_id, client_id)

    # Check budget
    if ctx.budget_remaining <= 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "BUDGET_EXCEEDED",
                "message": (
                    f"Monthly token budget of {ctx.monthly_token_budget:,} "
                    "has been exhausted."
                ),
                "tokens_used": ctx.tokens_used_this_month,
                "budget": ctx.monthly_token_budget,
            },
        )

    # ── Langfuse trace (silently skipped if not configured) ─────────────────────
    lf = get_langfuse()
    lf_trace = None
    lf_generation = None
    if lf:
        try:
            # M-09: anonymize user_id before sending to third-party Langfuse
            from app.core.compliance.anonymizer import hash_identifier
            anon_user = hash_identifier(str(current_user.id), str(agency_id))
            lf_trace = lf.trace(
                name="ai_chat",
                user_id=anon_user,
                metadata={
                    "agency_id": hash_identifier(str(agency_id), "langfuse"),
                    "agent_type": payload.agent_type,
                },
            )
        except Exception:
            lf_trace = None

    # call OpenRouter API
    try:
        from app.core.config import settings
        import httpx

        model: str = settings.OPENROUTER_TEXT_MODEL

        response_text = "[AI response - configure OPENROUTER_API_KEY to enable]"
        prompt_tokens = 0
        completion_tokens = 0

        if settings.OPENROUTER_API_KEY:
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            }
            messages = [
                {
                    "role": "system",
                    "content": (
                        f"You are an AI assistant for "
                        f"{ctx.brand_name or 'a marketing agency'}. "
                        f"Industry: {ctx.industry or 'marketing'}. "
                        f"Audience: {ctx.target_audience or 'general'}."
                    ),
                },
                {"role": "user", "content": payload.prompt},
            ]

            # Langfuse generation span
            if lf_trace:
                try:
                    lf_generation = lf_trace.generation(
                        name="openrouter_call",
                        model=model,
                        input=messages,
                    )
                except Exception:
                    lf_generation = None

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json={"model": model, "messages": messages},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    response_text = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)

        total_tokens = prompt_tokens + completion_tokens

        # Langfuse: end generation span
        if lf_generation:
            try:
                lf_generation.end(
                    output=response_text,
                    usage={
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens,
                    },
                )
            except Exception:
                pass

        # record token usage
        if total_tokens > 0:
            usage_record = TokenUsage(
                agency_id=agency_id,
                client_id=client_id,
                user_id=current_user.id,
                model=model,
                agent_type=payload.agent_type,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )
            db.add(usage_record)
            await db.commit()

        return AIResponse(
            agent_type=payload.agent_type,
            result=response_text,
            model=model,
            tokens_used=total_tokens,
            budget_remaining=max(0, ctx.budget_remaining - total_tokens),
        )

    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("AI chat error: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")  # H-2: do not leak internal exception


@router.get("/usage/monthly", response_model=MonthlyUsageSummary)
async def get_monthly_usage(
    db: AsyncSession = Depends(get_tenant_db),
    platform_db: AsyncSession = Depends(get_platform_db),
    current_user: User = Depends(get_current_user),
) -> MonthlyUsageSummary:
    """get currentmonth token usagesummary。"""
    agency_id: uuid.UUID = current_user.agency_id
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # totalusage
    result = await db.execute(
        select(
            func.coalesce(func.sum(TokenUsage.total_tokens), 0).label("total_tokens"),
            func.coalesce(func.sum(TokenUsage.cost_usd), 0.0).label("total_cost"),
        )
        .where(TokenUsage.agency_id == agency_id)
        .where(TokenUsage.created_at >= month_start)
    )
    row = result.first()
    total_tokens = int(row.total_tokens) if row else 0
    total_cost = float(row.total_cost) if row else 0.0

    # Group by model
    by_model_result = await db.execute(
        select(
            TokenUsage.model,
            func.sum(TokenUsage.total_tokens).label("tokens"),
        )
        .where(TokenUsage.agency_id == agency_id)
        .where(TokenUsage.created_at >= month_start)
        .group_by(TokenUsage.model)
    )
    by_model = {r.model: int(r.tokens) for r in by_model_result}

    # Group by agent
    by_agent_result = await db.execute(
        select(
            TokenUsage.agent_type,
            func.sum(TokenUsage.total_tokens).label("tokens"),
        )
        .where(TokenUsage.agency_id == agency_id)
        .where(TokenUsage.created_at >= month_start)
        .group_by(TokenUsage.agent_type)
    )
    by_agent = {(r.agent_type or "unknown"): int(r.tokens) for r in by_agent_result}

    # Agency budget — Agency rows live on the platform DB.
    agency = await platform_db.get(Agency, agency_id)
    budget = agency.monthly_token_budget if agency else 1_000_000

    return MonthlyUsageSummary(
        agency_id=str(agency_id),
        month=month_start.strftime("%Y-%m"),
        total_tokens=total_tokens,
        total_cost_usd=total_cost,
        budget=budget,
        budget_remaining=max(0, budget - total_tokens),
        by_model=by_model,
        by_agent=by_agent,
    )
