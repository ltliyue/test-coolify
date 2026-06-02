from __future__ import annotations
"""Attribution Agent — Pillar 3 attribution measurement."""
import json
import logging
from typing import Any, Dict

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an expert marketing attribution analyst.
Analyze the marketing data and generate an attribution report.

The report must include:
1. Channel performance breakdown (impressions, clicks, conversions, spend, ROI per channel)
2. Multi-touch attribution weights for each channel
3. Key insights and recommendations
4. Suggested budget reallocation

Respond ONLY with valid JSON in this format:
{
  "attribution_model": "multi_touch",
  "channels": [
    {
      "name": "Meta Ads",
      "impressions": 0,
      "clicks": 0,
      "conversions": 0,
      "spend": 0.0,
      "revenue": 0.0,
      "roi": 0.0,
      "attribution_weight": 0.0
    }
  ],
  "total_spend": 0.0,
  "total_revenue": 0.0,
  "overall_roi": 0.0,
  "top_performing_channel": "...",
  "recommendations": [
    "..."
  ],
  "budget_reallocation": {
    "channel_name": 0.0
  }
}
"""

_MOCK_OUTPUT: Dict[str, Any] = {
    "type": "attribution",
    "attribution_model": "multi_touch",
    "channels": [
        {
            "name": "Meta Ads",
            "impressions": 150000,
            "clicks": 4500,
            "conversions": 225,
            "spend": 3500.00,
            "revenue": 11250.00,
            "roi": 2.21,
            "attribution_weight": 0.35,
        },
        {
            "name": "Google Ads (GA4)",
            "impressions": 200000,
            "clicks": 6000,
            "conversions": 180,
            "spend": 4200.00,
            "revenue": 9000.00,
            "roi": 1.14,
            "attribution_weight": 0.30,
        },
        {
            "name": "Email (HubSpot)",
            "impressions": 50000,
            "clicks": 2500,
            "conversions": 375,
            "spend": 500.00,
            "revenue": 18750.00,
            "roi": 36.50,
            "attribution_weight": 0.25,
        },
        {
            "name": "Organic Social",
            "impressions": 80000,
            "clicks": 1600,
            "conversions": 80,
            "spend": 0.00,
            "revenue": 4000.00,
            "roi": 0.0,
            "attribution_weight": 0.10,
        },
    ],
    "total_spend": 8200.00,
    "total_revenue": 43000.00,
    "overall_roi": 4.24,
    "top_performing_channel": "Email (HubSpot)",
    "recommendations": [
        "Increase email campaign frequency — highest ROI channel at 36.5x",
        "Optimize Meta Ads targeting — strong ROI but room for improvement",
        "Review Google Ads keyword strategy — ROI below portfolio average",
        "Invest in organic social content — zero-cost channel driving conversions",
    ],
    "budget_reallocation": {
        "Meta Ads": 0.30,
        "Google Ads": 0.25,
        "Email": 0.35,
        "Organic Social": 0.10,
    },
}


def _query_warehouse_summary(agency_id: str) -> Dict[str, Any]:
    """from DuckDB query actualdatasummary（no data when returnempty dict）。"""
    try:
        from app.core.warehouse_client import get_warehouse
        wh = get_warehouse()

        meta_data = wh.query(
            "SELECT COUNT(*) as cnt, SUM(impressions) as imp, SUM(clicks) as clk, SUM(spend) as spd "
            "FROM raw_meta_ads WHERE agency_id = ?",
            [agency_id],
        )
        ga4_data = wh.query(
            "SELECT COUNT(*) as cnt, SUM(sessions) as sess, SUM(users) as usr "
            "FROM raw_ga4_events WHERE agency_id = ?",
            [agency_id],
        )
        hubspot_data = wh.query(
            "SELECT COUNT(*) as cnt FROM raw_hubspot_contacts WHERE agency_id = ?",
            [agency_id],
        )

        return {
            "meta_ads": meta_data[0] if meta_data else {},
            "ga4": ga4_data[0] if ga4_data else {},
            "hubspot": hubspot_data[0] if hubspot_data else {},
        }
    except Exception as e:
        log.debug("Warehouse query failed (expected in dev): %s", e)
        return {}


async def run(request: Any, ctx: Any) -> Dict[str, Any]:
    model = settings.ATTRIBUTION_MODEL
    prompt_tokens = 0
    completion_tokens = 0

    # attemptfrom warehousefetch realdata
    warehouse_data = _query_warehouse_summary(ctx.agency_id)

    if not settings.OPENROUTER_API_KEY:
        log.info("Attribution Agent: no API key, returning mock data")
        return {
            "output": _MOCK_OUTPUT,
            "model": model,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    brand_info = []
    if ctx.brand_name:
        brand_info.append(f"Brand: {ctx.brand_name}")
    if ctx.industry:
        brand_info.append(f"Industry: {ctx.industry}")

    user_msg = request.prompt
    if brand_info:
        user_msg = "Brand Context:\n" + "\n".join(brand_info) + "\n\n"

    if warehouse_data:
        user_msg += "Available Data Summary:\n" + json.dumps(warehouse_data, indent=2, default=str) + "\n\n"

    user_msg += "Request:\n" + request.prompt

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={"model": model, "messages": messages, "response_format": {"type": "json_object"}},
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)

                try:
                    output = json.loads(content)
                    output["type"] = "attribution"
                except json.JSONDecodeError:
                    output = {"type": "attribution", "raw_response": content}
            else:
                log.warning("Attribution Agent: OpenRouter returned %d", resp.status_code)
                output = _MOCK_OUTPUT
    except Exception as e:
        log.warning("Attribution Agent error: %s", e)
        output = _MOCK_OUTPUT

    cost = (prompt_tokens * 3 + completion_tokens * 15) / 1_000_000

    return {
        "output": output,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "estimated_cost_usd": cost,
    }
