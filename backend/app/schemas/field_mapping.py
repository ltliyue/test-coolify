from __future__ import annotations
import json
from typing import Optional, Any, Literal
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


# L-02: cap field-mapping expression/config length to defend against DoS
_MAX_TRANSFORM_CONFIG_SIZE = 4096  # bytes
_MAX_MAPPINGS_PER_UPDATE = 200


class TransformRule(BaseModel):
    type: Literal["value_mapping", "unit_conversion", "formula"]
    config: dict

    @field_validator("config")
    @classmethod
    def config_size_limit(cls, v: dict) -> dict:
        """L-02: bound the transform-config JSON size to defend against DoS."""
        size = len(json.dumps(v, default=str))
        if size > _MAX_TRANSFORM_CONFIG_SIZE:
            raise ValueError(f"Transform config too large ({size} bytes, max {_MAX_TRANSFORM_CONFIG_SIZE})")
        return v


class MappingEntry(BaseModel):
    source_field: Optional[str] = None
    target_field: str
    transform: Optional[TransformRule] = None


class FieldMappingCreate(BaseModel):
    platform: str
    name: Optional[str] = None
    integration_id: Optional[str] = None
    use_default_template: bool = True

    @field_validator("platform")
    @classmethod
    def platform_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Platform cannot be empty")
        return v.strip()


class FieldMappingUpdate(BaseModel):
    name: Optional[str] = None
    mappings: list[MappingEntry]
    change_summary: Optional[str] = None

    @field_validator("mappings")
    @classmethod
    def mappings_count_limit(cls, v: list) -> list:
        """L-02: cap the number of mapping entries per update."""
        if len(v) > _MAX_MAPPINGS_PER_UPDATE:
            raise ValueError(f"Too many mappings ({len(v)}, max {_MAX_MAPPINGS_PER_UPDATE})")
        return v


class PreviewRequest(BaseModel):
    mappings: list[MappingEntry]
    sample_data: Optional[list[dict[str, Any]]] = None


class PreviewRowResponse(BaseModel):
    source: dict[str, Any]
    transformed: dict[str, Any]
    warnings: list[str]


class FieldMappingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    agency_id: uuid.UUID
    platform: Optional[str]
    name: str
    mapping_config: dict[str, Any]
    current_version: int
    integration_id: Optional[uuid.UUID]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class FieldMappingVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    field_mapping_id: uuid.UUID
    version: int
    mapping_config: dict[str, Any]
    changed_by: Optional[uuid.UUID]
    change_summary: Optional[str]
    created_at: datetime


class CanonicalFieldResponse(BaseModel):
    name: str
    type: str
    category: str
    description: str


class RawFieldResponse(BaseModel):
    name: str
    type: str
    sample: Optional[Any] = None
    category: Optional[str] = None
    description: Optional[str] = None
