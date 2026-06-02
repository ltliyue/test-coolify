from __future__ import annotations
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.tenant_db import get_tenant_db
from app.models.user import User
from app.models.persona import Persona
from app.schemas.persona import (
    PersonaCreate, PersonaUpdate, PersonaResponse, PersonaGenerateRequest,
)
from app.schemas.audience_export import (
    AudienceExportRequest, AudienceExportPreview, AudienceExportResponse,
    VALID_EXPORT_PLATFORMS,
)
from app.models.audience_export import AudienceExport

router = APIRouter(prefix="/personas", tags=["personas"])


@router.get("", response_model=List[PersonaResponse])
async def list_personas(
    source: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="persona.list",
        actor=user,
        agency_id=user.agency_id,
    )
    stmt = select(Persona).where(
        Persona.agency_id == user.agency_id,
        Persona.is_active == True,  # noqa: E712
    )
    if source:
        stmt = stmt.where(Persona.source == source)
    stmt = stmt.order_by(Persona.created_at.desc())
    result = await db.execute(stmt)
    return [PersonaResponse.model_validate(p) for p in result.scalars().all()]


@router.post("", response_model=PersonaResponse, status_code=status.HTTP_201_CREATED)
async def create_persona(
    body: PersonaCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    p = Persona(
        agency_id=user.agency_id,
        name=body.name,
        description=body.description,
        psychographics=body.psychographics,
        channel_preferences=body.channel_preferences,
        recommended_tone=body.recommended_tone,
        source="manual",
    )
    db.add(p)
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="persona.create",
        actor=user,
        agency_id=user.agency_id,
    )
    await db.commit()
    await db.refresh(p)
    return PersonaResponse.model_validate(p)


@router.post("/generate", response_model=List[PersonaResponse])
async def generate_personas(
    body: PersonaGenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    from app.services.ai.context import build_shared_context
    from app.services.ai.agents import persona as persona_agent
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="persona.generate",
        actor=user,
        agency_id=user.agency_id,
    )

    ctx = await build_shared_context(db, user.agency_id)

    # Check budget
    if ctx.budget_remaining <= 0:
        raise HTTPException(status_code=429, detail="Monthly token budget exhausted")

    # Build the request object for the persona agent
    class _Req:
        prompt = body.prompt
        agent = "persona"
        agency_id = user.agency_id
        client_id = uuid.UUID(body.client_id) if body.client_id else None
        user_id = user.id
        context = {}
        request_id = str(uuid.uuid4())

    result = await persona_agent.run(_Req(), ctx)
    output = result.get("output", {})
    model_name = result.get("model", "")
    persona_list = output.get("personas", [])

    created: List[PersonaResponse] = []
    for pdata in persona_list[:body.count]:
        p = Persona(
            agency_id=user.agency_id,
            name=pdata.get("name", "Unnamed Persona"),
            description=pdata.get("description"),
            psychographics=pdata.get("psychographics"),
            channel_preferences=pdata.get("channel_preferences"),
            recommended_tone=pdata.get("recommended_tone"),
            source="ai",
            model_used=model_name,
        )
        db.add(p)
        await db.flush()
        await db.refresh(p)
        created.append(PersonaResponse.model_validate(p))

    await db.commit()
    return created


@router.get("/{persona_id}", response_model=PersonaResponse)
async def get_persona(
    persona_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    result = await db.execute(
        select(Persona).where(
            Persona.id == persona_id,
            Persona.agency_id == user.agency_id,
            Persona.is_active == True,  # noqa: E712
        )
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Persona not found")
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="persona.read",
        actor=user,
        agency_id=user.agency_id,
        resource=str(persona_id,
    ))
    await db.commit()
    return PersonaResponse.model_validate(p)


@router.put("/{persona_id}", response_model=PersonaResponse)
async def update_persona(
    persona_id: uuid.UUID,
    body: PersonaUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    result = await db.execute(
        select(Persona).where(
            Persona.id == persona_id,
            Persona.agency_id == user.agency_id,
            Persona.is_active == True,  # noqa: E712
        )
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Persona not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(p, field, value)
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="persona.update",
        actor=user,
        agency_id=user.agency_id,
        resource=str(persona_id,
    ))
    await db.commit()
    await db.refresh(p)
    return PersonaResponse.model_validate(p)


@router.delete("/{persona_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_persona(
    persona_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    result = await db.execute(
        select(Persona).where(
            Persona.id == persona_id,
            Persona.agency_id == user.agency_id,
            Persona.is_active == True,  # noqa: E712
        )
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Persona not found")
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="persona.delete",
        actor=user,
        agency_id=user.agency_id,
        resource=str(persona_id,
    ))
    p.is_active = False
    await db.commit()


# ── Persona-to-Audience Export ────────────────────────────

@router.get("/{persona_id}/export-audience/preview", response_model=AudienceExportPreview)
async def preview_audience_export(
    persona_id: uuid.UUID,
    platform: str = Query(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    """Preview the persona's conversion to a platform targeting spec (does not call the platform API)."""
    if platform not in VALID_EXPORT_PLATFORMS:
        raise HTTPException(status_code=400, detail=f"Invalid platform. Valid: {VALID_EXPORT_PLATFORMS}")

    result = await db.execute(
        select(Persona).where(
            Persona.id == persona_id,
            Persona.agency_id == user.agency_id,
            Persona.is_active == True,  # noqa: E712
        )
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="persona_export.preview",
        actor=user,
        agency_id=user.agency_id,
        resource=str(persona_id,
    ))
    await db.commit()

    from app.services.audience_export.translator import PersonaToTargetingTranslator
    translator = PersonaToTargetingTranslator()
    spec, warnings = translator.translate(
        persona.name, persona.psychographics, persona.channel_preferences, platform
    )
    return AudienceExportPreview(
        platform=platform, persona_name=persona.name,
        targeting_spec=spec, warnings=warnings,
    )


@router.post("/{persona_id}/export-audience", response_model=AudienceExportResponse, status_code=status.HTTP_201_CREATED)
async def create_audience_export(
    persona_id: uuid.UUID,
    body: AudienceExportRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    """initiate persona → platform audience export（async Celery task execute）。"""
    if body.platform not in VALID_EXPORT_PLATFORMS:
        raise HTTPException(status_code=400, detail=f"Invalid platform. Valid: {VALID_EXPORT_PLATFORMS}")

    result = await db.execute(
        select(Persona).where(
            Persona.id == persona_id,
            Persona.agency_id == user.agency_id,
            Persona.is_active == True,  # noqa: E712
        )
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    # generate targeting spec（PII already in translator  filter）
    from app.services.audience_export.translator import PersonaToTargetingTranslator
    translator = PersonaToTargetingTranslator()
    spec, _ = translator.translate(
        persona.name, persona.psychographics, persona.channel_preferences,
        body.platform, body.audience_name,
    )

    export = AudienceExport(
        agency_id=user.agency_id,
        persona_id=persona_id,
        platform=body.platform,
        targeting_spec=spec,
        status="pending",
    )
    db.add(export)
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="persona_export.create",
        actor=user,
        agency_id=user.agency_id,
    )
    await db.commit()
    await db.refresh(export)

    # Trigger async Celery task (skipped in test env)
    import os
    if os.getenv("TESTING") != "true":
        from app.tasks.audience_tasks import execute_audience_export_task
        execute_audience_export_task.delay(str(export.id), str(user.agency_id))

    return AudienceExportResponse.model_validate(export)


@router.get("/{persona_id}/export-audience", response_model=List[AudienceExportResponse])
async def list_persona_exports(
    persona_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    """Query the export history for a specific persona."""
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="persona_export.list",
        actor=user,
        agency_id=user.agency_id,
    )
    stmt = select(AudienceExport).where(
        AudienceExport.persona_id == persona_id,
        AudienceExport.agency_id == user.agency_id,
    ).order_by(AudienceExport.created_at.desc())
    result = await db.execute(stmt)
    return [AudienceExportResponse.model_validate(e) for e in result.scalars().all()]


@router.get("/audience-exports", response_model=List[AudienceExportResponse])
async def list_all_exports(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    """listcurrent agency all audience exportrecord。"""
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="persona_export.list_all",
        actor=user,
        agency_id=user.agency_id,
    )
    stmt = select(AudienceExport).where(
        AudienceExport.agency_id == user.agency_id,
    ).order_by(AudienceExport.created_at.desc()).limit(100)
    result = await db.execute(stmt)
    return [AudienceExportResponse.model_validate(e) for e in result.scalars().all()]
