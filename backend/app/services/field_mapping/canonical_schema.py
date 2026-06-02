from __future__ import annotations
from enum import Enum
from typing import Any, Optional


class FieldType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"


CANONICAL_FIELDS: list[dict[str, Any]] = [
    # Campaign Info
    {"name": "campaign_id", "type": FieldType.STRING, "category": "campaign", "description": "Campaign unique identifier"},
    {"name": "campaign_name", "type": FieldType.STRING, "category": "campaign", "description": "Campaign display name"},
    {"name": "campaign_status", "type": FieldType.STRING, "category": "campaign", "description": "Campaign status (active/paused/completed)"},
    # Ad Info
    {"name": "ad_id", "type": FieldType.STRING, "category": "ad", "description": "Ad unique identifier"},
    {"name": "ad_name", "type": FieldType.STRING, "category": "ad", "description": "Ad display name"},
    {"name": "ad_group", "type": FieldType.STRING, "category": "ad", "description": "Ad group or ad set name"},
    # Metrics
    {"name": "impressions", "type": FieldType.INTEGER, "category": "metrics", "description": "Number of impressions"},
    {"name": "clicks", "type": FieldType.INTEGER, "category": "metrics", "description": "Number of clicks"},
    {"name": "cost", "type": FieldType.FLOAT, "category": "metrics", "description": "Total spend/cost in dollars"},
    {"name": "conversions", "type": FieldType.INTEGER, "category": "metrics", "description": "Number of conversions"},
    {"name": "ctr", "type": FieldType.FLOAT, "category": "metrics", "description": "Click-through rate (%)"},
    {"name": "cpm", "type": FieldType.FLOAT, "category": "metrics", "description": "Cost per mille (per 1000 impressions)"},
    {"name": "cpc", "type": FieldType.FLOAT, "category": "metrics", "description": "Cost per click"},
    {"name": "conversion_value", "type": FieldType.FLOAT, "category": "metrics", "description": "Total conversion value"},
    {"name": "roas", "type": FieldType.FLOAT, "category": "metrics", "description": "Return on ad spend"},
    # Time
    {"name": "date", "type": FieldType.DATE, "category": "time", "description": "Report date"},
    {"name": "hour", "type": FieldType.INTEGER, "category": "time", "description": "Hour of day (0-23)"},
    # Audience
    {"name": "age", "type": FieldType.STRING, "category": "audience", "description": "Age range"},
    {"name": "gender", "type": FieldType.STRING, "category": "audience", "description": "Gender"},
    {"name": "location", "type": FieldType.STRING, "category": "audience", "description": "Geographic location"},
    {"name": "device", "type": FieldType.STRING, "category": "audience", "description": "Device type"},
    # Custom
    {"name": "custom_1", "type": FieldType.STRING, "category": "custom", "description": "Custom field 1"},
    {"name": "custom_2", "type": FieldType.STRING, "category": "custom", "description": "Custom field 2"},
    {"name": "custom_3", "type": FieldType.FLOAT, "category": "custom", "description": "Custom numeric field 3"},
]


def get_canonical_field(name: str) -> Optional[dict[str, Any]]:
    """Look up a canonical field by name."""
    for field in CANONICAL_FIELDS:
        if field["name"] == name:
            return field
    return None


def get_canonical_type(name: str) -> Optional[FieldType]:
    """Get the expected type for a canonical field."""
    field = get_canonical_field(name)
    return field["type"] if field else None
