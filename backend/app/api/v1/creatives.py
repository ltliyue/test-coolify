from __future__ import annotations
"""Creatives API — creative content generation endpoint."""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.tenant_db import get_tenant_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.creative import (
    Generation,
    GenerationResult,
    GenerationStatus,
    ResultStatus,
    TargetPlatform,
)
from app.schemas.creative import GenerationCreate, GenerationResponse

router = APIRouter(prefix="/creatives", tags=["creatives"])


@router.post("/generate", response_model=GenerationResponse)
async def generate_creative(
    body: GenerationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
) -> GenerationResponse:
    """Create a Generation record and call the Creative Agent to generate creative content."""
    from app.services.ai.context import build_shared_context
    from app.services.ai.agents import creative as creative_agent

    ctx = await build_shared_context(db, user.agency_id)

    if ctx.budget_remaining <= 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Monthly token budget exhausted",
        )

    # create Generation record
    gen = Generation(
        agency_id=user.agency_id,
        user_id=user.id,
        prompt=body.prompt,
        status=GenerationStatus.PROCESSING,
        agent_type="creative",
    )
    db.add(gen)
    await db.flush()

    # Build the request object for the agent
    class _AgentReq:
        def __init__(self, prompt: str, client_id: Optional[str]) -> None:
            self.prompt = prompt
            self.agent = "creative"
            self.agency_id = user.agency_id
            self.client_id = uuid.UUID(client_id) if client_id else None
            self.user_id = user.id
            self.context: dict = {}
            self.request_id = str(uuid.uuid4())

    try:
        result = await creative_agent.run(_AgentReq(body.prompt, body.client_id), ctx)
        output = result.get("output", {})
        creatives = output.get("creatives", [])

        # to eachplatformcreate result
        for creative_data in creatives:
            platform_str = creative_data.get("platform", "INSTAGRAM").upper()
            try:
                platform_enum = TargetPlatform(platform_str)
            except ValueError:
                continue

            if platform_str not in [p.upper() for p in body.platforms]:
                continue

            gr = GenerationResult(
                generation_id=gen.id,
                platform=platform_enum,
                copy_text=creative_data.get("copy_text"),
                status=ResultStatus.COMPLETED,
            )
            db.add(gr)

        gen.status = GenerationStatus.COMPLETED
        gen.metadata_ = {"strategy_notes": output.get("strategy_notes", "")}

    except Exception as e:
        gen.status = GenerationStatus.FAILED
        import logging as _log_mod
        _log_mod.getLogger(__name__).error("Creative generation failed: %s", e)
        gen.error_message = "Generation failed"  # H-05: do not leak internal exceptions to DB/API

    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="creative.generate",
        actor=user,
        agency_id=user.agency_id,
        resource=str(gen.id,
    ))
    await db.commit()

    # re-query to load results
    stmt = (
        select(Generation)
        .where(Generation.id == gen.id)
        .options(selectinload(Generation.results))
    )
    row = await db.execute(stmt)
    gen = row.scalar_one()
    return GenerationResponse.model_validate(gen)


@router.get("", response_model=List[GenerationResponse])
async def list_generations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
) -> List[GenerationResponse]:
    """listcurrent agency generations。"""
    stmt = (
        select(Generation)
        .where(Generation.agency_id == user.agency_id)
        .options(selectinload(Generation.results))
        .order_by(Generation.created_at.desc())
        .limit(50)
    )
    result = await db.execute(stmt)
    return [GenerationResponse.model_validate(g) for g in result.scalars().all()]


@router.get("/{generation_id}", response_model=GenerationResponse)
async def get_generation(
    generation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
) -> GenerationResponse:
    """get single generation（containing results）。"""
    stmt = (
        select(Generation)
        .where(
            Generation.id == generation_id,
            Generation.agency_id == user.agency_id,
        )
        .options(selectinload(Generation.results))
    )
    result = await db.execute(stmt)
    gen = result.scalar_one_or_none()
    if not gen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation not found",
        )
    return GenerationResponse.model_validate(gen)
