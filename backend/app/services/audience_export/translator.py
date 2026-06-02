from __future__ import annotations
"""Persona → ad-platform targeting spec converter.

Compliance requirements:
- Only output Level 0 aggregate attributes (interests / age range / geography)
- Explicitly filter Level 2+ PII fields (email/phone/name/ip/device_id)
"""
import logging
from typing import Optional

log = logging.getLogger(__name__)

# Level 2+ PII field block-list — never passed to ad platforms
_PII_FIELDS = {
    "email", "phone", "name", "full_name", "first_name", "last_name",
    "ip", "ip_address", "device_id", "cookie_id", "ssn", "address",
    "date_of_birth", "medical_record", "health_plan_number",
}


def _strip_pii(data: Optional[dict]) -> dict:
    """recursively remove PII fields，return clean dict。"""
    if not data:
        return {}
    clean = {}
    for key, value in data.items():
        if key.lower() in _PII_FIELDS:
            log.info("PII field stripped from targeting spec: %s", key)
            continue
        if isinstance(value, dict):
            clean[key] = _strip_pii(value)
        else:
            clean[key] = value
    return clean


class PersonaToTargetingTranslator:
    """convert Persona  structured attributeconvertto platform targeting spec。"""

    def translate(self, persona_name: str, psychographics: Optional[dict],
                  channel_preferences: Optional[dict], platform: str,
                  audience_name: Optional[str] = None) -> tuple[dict, list[str]]:
        """
        return (targeting_spec, warnings)。
        targeting_spec only contains Level 0 data。
        """
        warnings = []
        clean_psycho = _strip_pii(psychographics)
        clean_channels = _strip_pii(channel_preferences)

        if not clean_psycho:
            warnings.append("Persona has no psychographics data — targeting will be broad")

        name = audience_name or f"ReceptivIQ: {persona_name}"

        if platform == "meta_ads":
            spec = self._to_meta_spec(name, clean_psycho, clean_channels)
        elif platform == "dv360":
            spec = self._to_dv360_spec(name, clean_psycho, clean_channels)
        else:
            raise ValueError(f"Unsupported platform: {platform}")

        return spec, warnings

    def _to_meta_spec(self, name: str, psycho: dict, channels: dict) -> dict:
        interests = psycho.get("interests", [])
        behaviors = psycho.get("behaviors", [])
        demographics = psycho.get("demographics", {})

        return {
            "name": name,
            "description": f"Auto-generated audience from ReceptivIQ persona",
            "targeting": {
                "geo_locations": {"countries": demographics.get("countries", ["US"])},
                "age_min": demographics.get("age_min", 18),
                "age_max": demographics.get("age_max", 65),
                "genders": demographics.get("genders", []),
                "interests": [
                    {"id": str(i), "name": str(i)} if isinstance(i, str)
                    else {"id": str(i.get("id", "")), "name": i.get("name", "")}
                    for i in interests
                ],
                "behaviors": [
                    {"id": str(b), "name": str(b)} if isinstance(b, str)
                    else {"id": str(b.get("id", "")), "name": b.get("name", "")}
                    for b in behaviors
                ],
            },
            "subtype": "CUSTOM",
        }

    def _to_dv360_spec(self, name: str, psycho: dict, channels: dict) -> dict:
        return {
            "displayName": name,
            "audienceType": "FIRST_PARTY",
            "membershipDurationDays": 30,
            "description": f"Auto-generated audience from ReceptivIQ persona",
            "firstAndThirdPartyAudienceInfo": {
                "appId": None,
            },
        }
