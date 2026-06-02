from __future__ import annotations
from app.models.enums import AuthType

PLATFORM_REGISTRY: dict[str, dict] = {
    "ga4": {
        "key": "ga4",
        "name": "Google Analytics 4",
        "description": "Connect Google Analytics 4 to sync website and app performance data.",
        "auth_type": AuthType.OAUTH,
        "icon": "ga4",
        "connect_fields": [],
    },
    "meta_ads": {
        "key": "meta_ads",
        "name": "Meta Ads",
        "description": "Connect Meta Ads to sync Facebook and Instagram campaign data.",
        "auth_type": AuthType.OAUTH,
        "icon": "meta_ads",
        "connect_fields": [],
    },
    "hubspot": {
        "key": "hubspot",
        "name": "HubSpot",
        "description": "Connect HubSpot CRM to sync contact and deal data.",
        "auth_type": AuthType.OAUTH,
        "icon": "hubspot",
        "connect_fields": [],
    },
    "tiktok_ads": {
        "key": "tiktok_ads",
        "name": "TikTok Ads",
        "description": "Connect TikTok Ads to sync campaign and creative performance data.",
        "auth_type": AuthType.OAUTH,
        "icon": "tiktok_ads",
        "connect_fields": [],
    },
    "dv360": {
        "key": "dv360",
        "name": "Display & Video 360",
        "description": "Connect DV360 to sync programmatic campaign data.",
        "auth_type": AuthType.API_KEY,
        "icon": "dv360",
        "connect_fields": [
            {
                "key": "api_key",
                "label": "API Key",
                "required": True,
                "secret": True,
            }
        ],
    },
    "stackadapt": {
        "key": "stackadapt",
        "name": "StackAdapt",
        "description": "Connect StackAdapt to sync native and programmatic ad data.",
        "auth_type": AuthType.API_KEY,
        "icon": "stackadapt",
        "connect_fields": [
            {
                "key": "api_key",
                "label": "API Key",
                "required": True,
                "secret": True,
            }
        ],
    },
    "leadrx": {
        "key": "leadrx",
        "name": "LeadrX",
        "description": "Connect LeadrX to sync lead attribution and conversion data.",
        "auth_type": AuthType.API_KEY,
        "icon": "leadrx",
        "connect_fields": [
            {
                "key": "api_key",
                "label": "API Key",
                "required": True,
                "secret": True,
            }
        ],
    },
    "liveramp": {
        "key": "liveramp",
        "name": "LiveRamp",
        "description": "Connect LiveRamp for identity resolution and data connectivity.",
        "auth_type": AuthType.API_KEY,
        "icon": "liveramp",
        "connect_fields": [
            {
                "key": "api_key",
                "label": "API Key",
                "required": True,
                "secret": True,
            }
        ],
    },
    "quorum": {
        "key": "quorum",
        "name": "Quorum",
        "description": "Connect Quorum to sync political and advocacy data.",
        "auth_type": AuthType.API_KEY,
        "icon": "quorum",
        "connect_fields": [
            {
                "key": "api_key",
                "label": "API Key",
                "required": True,
                "secret": True,
            }
        ],
    },
    # ── New platforms (Discovery doc Stage-6 Step-1) — adapter not implemented yet ──
    "trade_desk": {
        "key": "trade_desk",
        "name": "The Trade Desk",
        "description": "Connect The Trade Desk DSP for programmatic campaign data across CTV, display, audio.",
        "auth_type": AuthType.API_KEY,
        "icon": "trade_desk",
        "status": "planned",  # adapter pending — see features/PROJECT-PLAN.md F-23
        "connect_fields": [
            {
                "key": "api_key",
                "label": "API Key",
                "required": True,
                "secret": True,
            },
            {
                "key": "partner_id",
                "label": "Partner ID",
                "required": True,
                "secret": False,
            },
        ],
    },
    "google_ads": {
        "key": "google_ads",
        "name": "Google Ads",
        "description": "Connect Google Ads to sync search campaign performance, separate from GA4.",
        "auth_type": AuthType.OAUTH,
        "icon": "google_ads",
        "status": "planned",  # adapter pending — see features/PROJECT-PLAN.md F-24
        "connect_fields": [],
    },
    "salesforce": {
        "key": "salesforce",
        "name": "Salesforce",
        "description": "Connect Salesforce CRM to sync accounts, contacts, opportunities, and activities.",
        "auth_type": AuthType.OAUTH,
        "icon": "salesforce",
        "status": "planned",  # adapter pending — see features/PROJECT-PLAN.md F-25
        "connect_fields": [],
    },
    "netsuite": {
        "key": "netsuite",
        "name": "Oracle NetSuite",
        "description": "Connect Oracle NetSuite ERP/CRM for customer and revenue data.",
        "auth_type": AuthType.OAUTH,
        "icon": "netsuite",
        "status": "planned",  # adapter pending — see features/PROJECT-PLAN.md F-26
        "connect_fields": [],
    },
    "placeriq": {
        "key": "placeriq",
        "name": "PlacerIQ",
        "description": "Connect PlacerIQ for location intelligence and foot-traffic analytics.",
        "auth_type": AuthType.API_KEY,
        "icon": "placeriq",
        "status": "planned",  # adapter pending — see features/PROJECT-PLAN.md F-27
        "connect_fields": [
            {
                "key": "api_key",
                "label": "API Key",
                "required": True,
                "secret": True,
            }
        ],
    },
    "experian": {
        "key": "experian",
        "name": "Experian",
        "description": "Connect Experian Syndicated Audiences for demographic and psychographic segmentation.",
        "auth_type": AuthType.API_KEY,
        "icon": "experian",
        "status": "planned",  # adapter pending — see features/PROJECT-PLAN.md F-28
        "connect_fields": [
            {
                "key": "api_key",
                "label": "API Key",
                "required": True,
                "secret": True,
            }
        ],
    },
    # ── Creative tooling (consumed by Creative Agent, not ETL sources) ──
    "adobe_firefly": {
        "key": "adobe_firefly",
        "name": "Adobe Firefly",
        "description": "Adobe Firefly API for generative image creation in Creative Agent outputs.",
        "auth_type": AuthType.API_KEY,
        "icon": "adobe_firefly",
        "status": "planned",  # creative tooling, not ETL — see features/PROJECT-PLAN.md F-29
        "category": "creative",
        "connect_fields": [
            {
                "key": "api_key",
                "label": "API Key",
                "required": True,
                "secret": True,
            }
        ],
    },
    "canva": {
        "key": "canva",
        "name": "Canva",
        "description": "Canva Connect API for template-based design generation in Creative Agent outputs.",
        "auth_type": AuthType.OAUTH,
        "icon": "canva",
        "status": "planned",  # creative tooling, not ETL — see features/PROJECT-PLAN.md F-30
        "category": "creative",
        "connect_fields": [],
    },
}


def get_platform_info(key: str) -> dict | None:
    return PLATFORM_REGISTRY.get(key)


def list_platforms() -> list[dict]:
    return list(PLATFORM_REGISTRY.values())
