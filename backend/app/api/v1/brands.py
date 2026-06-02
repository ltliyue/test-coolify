from __future__ import annotations
"""F-13 brand onboarding API — store/read Agency brand config."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_db import get_tenant_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.agency import Agency
from app.schemas.brand import BrandConfigUpdate, BrandConfigResponse

router = APIRouter(prefix="/brands", tags=["brands"])


def _config_to_response(agency_id: uuid.UUID, config: dict) -> BrandConfigResponse:
    return BrandConfigResponse(
        agency_id=str(agency_id),
        name=config.get("name"),
        logo_url=config.get("logo_url"),
        primary_color=config.get("primary_color"),
        secondary_color=config.get("secondary_color"),
        brand_voice=config.get("brand_voice"),
        industry=config.get("industry"),
        target_audience=config.get("target_audience"),
        website_url=config.get("website_url"),
        tagline=config.get("tagline"),
    )


@router.get("/config", response_model=BrandConfigResponse)
async def get_brand_config(
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> BrandConfigResponse:
    """Get the current agency's brand config."""
    agency = await db.get(Agency, current_user.agency_id)
    if not agency:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found")
    config = agency.brand_config or {}
    return _config_to_response(current_user.agency_id, config)


@router.put("/config", response_model=BrandConfigResponse)
async def update_brand_config(
    payload: BrandConfigUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> BrandConfigResponse:
    """Update brand config (partial update; fields not provided remain unchanged)."""
    agency = await db.get(Agency, current_user.agency_id)
    if not agency:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found")

    # Merge update (PATCH semantics: only overrides non-None fields)
    config = dict(agency.brand_config or {})
    for field, value in payload.model_dump(exclude_none=True).items():
        config[field] = value

    agency.brand_config = config
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="brand.update",
        actor=current_user,
        agency_id=current_user.agency_id,
        resource=str(current_user.agency_id,
    ))
    await db.commit()
    await db.refresh(agency)
    return _config_to_response(current_user.agency_id, agency.brand_config or {})


@router.delete("/config", status_code=status.HTTP_204_NO_CONTENT)
async def reset_brand_config(
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Clear brand config (reset to empty)."""
    agency = await db.get(Agency, current_user.agency_id)
    if not agency:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found")
    agency.brand_config = {}
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="brand.reset",
        actor=current_user,
        agency_id=current_user.agency_id,
        resource=str(current_user.agency_id,
    ))
    await db.commit()
