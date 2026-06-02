from __future__ import annotations
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_db import get_tenant_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.field_mapping import FieldMapping, FieldMappingVersion
from app.schemas.field_mapping import (
    FieldMappingCreate,
    FieldMappingUpdate,
    FieldMappingResponse,
    FieldMappingVersionResponse,
    PreviewRequest,
    PreviewRowResponse,
    CanonicalFieldResponse,
    RawFieldResponse,
)
from app.services.field_mapping.canonical_schema import CANONICAL_FIELDS
from app.services.field_mapping.template_loader import (
    get_raw_fields,
    get_default_mappings,
    list_supported_platforms,
    load_template,
)
from app.services.field_mapping.transform import TransformEngine

router = APIRouter(prefix="/field-mappings", tags=["field-mappings"])


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def _get_user_mapping(
    mapping_id: uuid.UUID, user: User, db: AsyncSession
) -> FieldMapping:
    """Fetch a field mapping scoped to agency + active."""
    result = await db.execute(
        select(FieldMapping).where(
            FieldMapping.id == mapping_id,
            FieldMapping.agency_id == user.agency_id,
            FieldMapping.is_active == True,  # noqa: E712
        )
    )
    mapping = result.scalar_one_or_none()
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Field mapping not found"
        )
    return mapping


# ---------------------------------------------------------------------------
# Static / platform routes — must be registered BEFORE /{mapping_id}
# ---------------------------------------------------------------------------

@router.get(
    "/canonical-schema",
    response_model=list[CanonicalFieldResponse],
)
async def get_canonical_schema(
    user: User = Depends(get_current_user),
) -> list[CanonicalFieldResponse]:
    """Return the full canonical field schema."""
    return [
        CanonicalFieldResponse(
            name=f["name"],
            type=f["type"].value if hasattr(f["type"], "value") else f["type"],
            category=f["category"],
            description=f["description"],
        )
        for f in CANONICAL_FIELDS
    ]


@router.get(
    "/platforms/{platform}/raw-fields",
    response_model=list[RawFieldResponse],
)
async def get_platform_raw_fields(
    platform: str,
    user: User = Depends(get_current_user),
) -> list[RawFieldResponse]:
    """Return the raw fields for a given platform."""
    supported = list_supported_platforms()
    if platform not in supported:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform '{platform}' not supported. Available: {supported}",
        )
    raw = get_raw_fields(platform)
    return [RawFieldResponse(**f) for f in raw]


@router.get(
    "/platforms/{platform}/default-template",
)
async def get_default_template(
    platform: str,
    user: User = Depends(get_current_user),
) -> dict:
    """Return the default mapping template for a platform."""
    supported = list_supported_platforms()
    if platform not in supported:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform '{platform}' not supported. Available: {supported}",
        )
    mappings = get_default_mappings(platform)
    return {"platform": platform, "mappings": mappings}


# ---------------------------------------------------------------------------
# CRUD routes
# ---------------------------------------------------------------------------

@router.get("", response_model=list[FieldMappingResponse])
async def list_field_mappings(
    platform: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
) -> list[FieldMappingResponse]:
    """List all field mappings for the current agency."""
    stmt = select(FieldMapping).where(
        FieldMapping.agency_id == user.agency_id,
        FieldMapping.is_active == True,  # noqa: E712
    )
    if platform:
        stmt = stmt.where(FieldMapping.platform == platform)
    stmt = stmt.order_by(FieldMapping.created_at.desc())

    result = await db.execute(stmt)
    mappings = result.scalars().all()
    return [FieldMappingResponse.model_validate(m) for m in mappings]


@router.post("", response_model=FieldMappingResponse, status_code=status.HTTP_201_CREATED)
async def create_field_mapping(
    body: FieldMappingCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
) -> FieldMappingResponse:
    """Create a new field mapping, optionally from a default template."""
    supported = list_supported_platforms()
    if body.platform not in supported:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platform '{body.platform}'. Supported: {supported}",
        )

    # Build mapping config
    if body.use_default_template:
        default_mappings = get_default_mappings(body.platform)
        mapping_config = {"mappings": default_mappings}
    else:
        mapping_config = {"mappings": []}

    name = body.name or f"{body.platform} mapping"
    integration_id = uuid.UUID(body.integration_id) if body.integration_id else None

    mapping = FieldMapping(
        agency_id=user.agency_id,
        user_id=user.id,
        integration_id=integration_id,
        platform=body.platform,
        name=name,
        mapping_config=mapping_config,
        current_version=1,
    )
    db.add(mapping)
    await db.flush()

    # Create initial version snapshot
    version = FieldMappingVersion(
        field_mapping_id=mapping.id,
        version=1,
        mapping_config=mapping_config,
        changed_by=user.id,
        change_summary="Initial mapping created",
    )
    db.add(version)
    await db.commit()
    await db.refresh(mapping)
    return FieldMappingResponse.model_validate(mapping)


@router.get("/{mapping_id}", response_model=FieldMappingResponse)
async def get_field_mapping(
    mapping_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
) -> FieldMappingResponse:
    """Get a single field mapping by ID."""
    mapping = await _get_user_mapping(mapping_id, user, db)
    return FieldMappingResponse.model_validate(mapping)


@router.put("/{mapping_id}", response_model=FieldMappingResponse)
async def update_field_mapping(
    mapping_id: uuid.UUID,
    body: FieldMappingUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
) -> FieldMappingResponse:
    """Update a field mapping. Creates a new version snapshot automatically."""
    mapping = await _get_user_mapping(mapping_id, user, db)

    # Build new mapping config from the submitted entries
    new_config = {
        "mappings": [entry.model_dump(mode="json") for entry in body.mappings]
    }

    # Bump version
    new_version_num = mapping.current_version + 1

    # Save version snapshot
    version = FieldMappingVersion(
        field_mapping_id=mapping.id,
        version=new_version_num,
        mapping_config=new_config,
        changed_by=user.id,
        change_summary=body.change_summary,
    )
    db.add(version)

    # Update the mapping itself
    mapping.mapping_config = new_config
    mapping.current_version = new_version_num
    if body.name is not None:
        mapping.name = body.name

    await db.commit()
    await db.refresh(mapping)
    return FieldMappingResponse.model_validate(mapping)


@router.delete("/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_field_mapping(
    mapping_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
) -> None:
    """Soft-delete a field mapping."""
    mapping = await _get_user_mapping(mapping_id, user, db)
    mapping.is_active = False
    await db.commit()


@router.get(
    "/{mapping_id}/versions",
    response_model=list[FieldMappingVersionResponse],
)
async def list_versions(
    mapping_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
) -> list[FieldMappingVersionResponse]:
    """List all versions for a field mapping."""
    # Ensure the mapping exists and belongs to the agency
    await _get_user_mapping(mapping_id, user, db)

    result = await db.execute(
        select(FieldMappingVersion)
        .where(FieldMappingVersion.field_mapping_id == mapping_id)
        .order_by(FieldMappingVersion.version.desc())
    )
    versions = result.scalars().all()
    return [FieldMappingVersionResponse.model_validate(v) for v in versions]


@router.post(
    "/{mapping_id}/versions/{version_id}/rollback",
    response_model=FieldMappingResponse,
)
async def rollback_to_version(
    mapping_id: uuid.UUID,
    version_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
) -> FieldMappingResponse:
    """Rollback a field mapping to a specific version."""
    mapping = await _get_user_mapping(mapping_id, user, db)

    # Find the target version
    result = await db.execute(
        select(FieldMappingVersion).where(
            FieldMappingVersion.id == version_id,
            FieldMappingVersion.field_mapping_id == mapping_id,
        )
    )
    target_version = result.scalar_one_or_none()
    if not target_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Version not found"
        )

    # Create a new version that copies the target version's config
    new_version_num = mapping.current_version + 1
    rollback_version = FieldMappingVersion(
        field_mapping_id=mapping.id,
        version=new_version_num,
        mapping_config=target_version.mapping_config,
        changed_by=user.id,
        change_summary=f"Rollback to version {target_version.version}",
    )
    db.add(rollback_version)

    # Update mapping to the rolled-back config
    mapping.mapping_config = target_version.mapping_config
    mapping.current_version = new_version_num

    await db.commit()
    await db.refresh(mapping)
    return FieldMappingResponse.model_validate(mapping)


@router.post(
    "/{mapping_id}/preview",
    response_model=list[PreviewRowResponse],
)
async def preview_transform(
    mapping_id: uuid.UUID,
    body: PreviewRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
) -> list[PreviewRowResponse]:
    """Preview the transform result using either provided sample data or template samples."""
    mapping = await _get_user_mapping(mapping_id, user, db)

    # Build the mapping config from the request
    config = {
        "mappings": [entry.model_dump(mode="json") for entry in body.mappings]
    }
    engine = TransformEngine(config)

    # Use provided sample data or generate sample rows from the platform template
    sample_rows = body.sample_data
    if not sample_rows:
        try:
            platform_name = mapping.platform if isinstance(mapping.platform, str) else str(mapping.platform)
            template = load_template(platform_name)
            raw_fields = template.get("raw_fields", [])
            # Build a sample row from the template's sample values
            sample_row = {f["name"]: f.get("sample") for f in raw_fields}
            sample_rows = [sample_row]
        except (ValueError, KeyError):
            sample_rows = [{"_note": "No sample data available"}]

    results = []
    for row in sample_rows:
        transformed, warnings = engine.transform_row(row)
        results.append(
            PreviewRowResponse(
                source=row,
                transformed=transformed,
                warnings=warnings,
            )
        )
    return results
