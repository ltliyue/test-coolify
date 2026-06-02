from __future__ import annotations
"""Persona Agent — Pillar 1 market research intelligence。"""
import json
import logging
from typing import Any, Dict

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an expert market researcher and audience strategist.
Based on the brand information and any available data, generate detailed marketing personas.

Each persona MUST include:
- name: A memorable name for the persona
- description: 2-3 sentence overview
- psychographics: object with values, interests, pain_points, motivations (arrays of strings)
- channel_preferences: object with preferred_channels, content_types, best_times (arrays of strings)
- recommended_tone: A short phrase describing the ideal communication tone

Respond ONLY with valid JSON in this format:
{
  "personas": [
    {
      "name": "...",
      "description": "...",
      "psychographics": {"values": [], "interests": [], "pain_points": [], "motivations": []},
      "channel_preferences": {"preferred_channels": [], "content_types": [], "best_times": []},
      "recommended_tone": "..."
    }
  ],
  "audience_blueprint": {
    "primary_segments": [],
    "key_insights": [],
    "recommended_channels": []
  }
}
"""

_MOCK_OUTPUT: Dict[str, Any] = {
    "type": "persona",
    "personas": [
        {
            "name": "Strategic Sarah",
            "description": "A data-driven marketing director who values measurable ROI and strategic planning.",
            "psychographics": {
                "values": ["efficiency", "data-driven decisions", "innovation"],
                "interests": ["marketing technology", "analytics", "industry trends"],
                "pain_points": ["budget constraints", "proving ROI", "team alignment"],
                "motivations": ["career growth", "team success", "industry recognition"],
            },
            "channel_preferences": {
                "preferred_channels": ["LinkedIn", "Email", "Webinars"],
                "content_types": ["case studies", "whitepapers", "data reports"],
                "best_times": ["Tuesday 9-11am", "Thursday 2-4pm"],
            },
            "recommended_tone": "Professional, data-backed, and solution-oriented",
        },
    ],
    "audience_blueprint": {
        "primary_segments": ["Marketing Directors", "Growth Managers"],
        "key_insights": ["Prefer data-backed content", "Active on LinkedIn"],
        "recommended_channels": ["LinkedIn", "Email newsletters"],
    },
}


async def run(request: Any, ctx: Any) -> Dict[str, Any]:
    """
    Execute Persona Agent:
    - with API key → call OpenRouter to generate persona
    - without API key → return mock data
    """
    model = settings.PERSONA_MODEL
    prompt_tokens = 0
    completion_tokens = 0

    if not settings.OPENROUTER_API_KEY:
        log.info("Persona Agent: no API key, returning mock data")
        return {
            "output": _MOCK_OUTPUT,
            "model": model,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    # build user prompt
    brand_info = []
    if ctx.brand_name:
        brand_info.append(f"Brand: {ctx.brand_name}")
    if ctx.industry:
        brand_info.append(f"Industry: {ctx.industry}")
    if ctx.target_audience:
        brand_info.append(f"Target Audience: {ctx.target_audience}")
    if ctx.brand_voice:
        brand_info.append(f"Brand Voice: {ctx.brand_voice}")

    user_msg = request.prompt
    if brand_info:
        user_msg = "Brand Context:\n" + "\n".join(brand_info) + "\n\nRequest:\n" + user_msg

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
                    output["type"] = "persona"
                except json.JSONDecodeError:
                    output = {"type": "persona", "raw_response": content}
            else:
                log.warning("Persona Agent: OpenRouter returned %d", resp.status_code)
                output = _MOCK_OUTPUT
    except Exception as e:
        log.warning("Persona Agent error: %s", e)
        output = _MOCK_OUTPUT

    # cost: Claude Opus ~$15/M input, $75/M output
    cost = (prompt_tokens * 15 + completion_tokens * 75) / 1_000_000

    return {
        "output": output,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "estimated_cost_usd": cost,
    }
