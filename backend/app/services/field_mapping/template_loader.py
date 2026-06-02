from __future__ import annotations
import json
from pathlib import Path

TEMPLATE_DIR = Path(__file__).parent / "templates"


def load_template(platform: str) -> dict:
    """Load a platform's default mapping template."""
    path = TEMPLATE_DIR / f"{platform}.json"
    if not path.exists():
        raise ValueError(f"No template for platform: {platform}")
    return json.loads(path.read_text())


def get_raw_fields(platform: str) -> list[dict]:
    """Get a platform's raw field metadata."""
    template = load_template(platform)
    return template["raw_fields"]


def get_default_mappings(platform: str) -> list[dict]:
    """Get a platform's default field mappings."""
    template = load_template(platform)
    return template["default_mappings"]


def list_supported_platforms() -> list[str]:
    """List all platforms that have templates."""
    return [p.stem for p in TEMPLATE_DIR.glob("*.json")]
