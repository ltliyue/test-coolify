from __future__ import annotations
"""Creative Agent — Pillar 2 creative content engine."""
import json
import logging
from typing import Any, Dict

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an expert creative copywriter and content strategist.
Generate platform-specific marketing content based on the brand information and user request.

For each target platform, generate:
- copy_text: The marketing copy optimized for that platform's audience and format constraints
- hashtags: Relevant hashtags (if applicable)
- cta: A call-to-action phrase
- tone: The tone used

Respond ONLY with valid JSON in this format:
{
  "creatives": [
    {
      "platform": "INSTAGRAM",
      "copy_text": "...",
      "hashtags": ["#...", "#..."],
      "cta": "...",
      "tone": "..."
    },
    {
      "platform": "FACEBOOK",
      "copy_text": "...",
      "hashtags": [],
      "cta": "...",
      "tone": "..."
    }
  ],
  "strategy_notes": "Brief notes on the creative strategy used"
}
"""

_PLATFORMS = ["INSTAGRAM", "FACEBOOK", "TIKTOK", "TWITTER"]

_MOCK_OUTPUT: Dict[str, Any] = {
    "type": "creative",
    "creatives": [
        {
            "platform": "INSTAGRAM",
            "copy_text": "Transform your marketing with AI-powered insights. Our platform delivers data-driven strategies that actually convert.",
            "hashtags": ["#MarketingAI", "#DataDriven", "#GrowthHacking"],
            "cta": "Start your free trial today",
            "tone": "Energetic and aspirational",
        },
        {
            "platform": "FACEBOOK",
            "copy_text": "Tired of guessing what works? Our AI marketing platform analyzes your data and creates campaigns that drive real results. See how agencies are 3x-ing their ROI.",
            "hashtags": [],
            "cta": "Learn More",
            "tone": "Professional and informative",
        },
        {
            "platform": "TIKTOK",
            "copy_text": "POV: You just discovered the marketing tool that does the thinking for you",
            "hashtags": ["#MarketingTok", "#AI", "#BusinessGrowth"],
            "cta": "Link in bio",
            "tone": "Casual and trendy",
        },
        {
            "platform": "TWITTER",
            "copy_text": "The future of marketing is here. AI-powered insights, better campaigns, higher ROI. Simple as that.",
            "hashtags": ["#MarTech", "#AI"],
            "cta": "Try it free",
            "tone": "Concise and bold",
        },
    ],
    "strategy_notes": "Multi-platform approach targeting different audience segments with platform-native content styles.",
}


async def run(request: Any, ctx: Any) -> Dict[str, Any]:
    """
    Execute the Creative Agent:
    - With API key -> call OpenRouter to generate creative content
    - Without API key -> return mock data
    """
    model = settings.CREATIVE_MODEL
    prompt_tokens = 0
    completion_tokens = 0

    if not settings.OPENROUTER_API_KEY:
        log.info("Creative Agent: no API key, returning mock data")
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
        brand_info.append("Brand: %s" % ctx.brand_name)
    if ctx.industry:
        brand_info.append("Industry: %s" % ctx.industry)
    if ctx.target_audience:
        brand_info.append("Target Audience: %s" % ctx.target_audience)
    if ctx.brand_voice:
        brand_info.append("Brand Voice: %s" % ctx.brand_voice)

    user_msg = request.prompt
    if brand_info:
        user_msg = "Brand Context:\n" + "\n".join(brand_info) + "\n\nRequest:\n" + user_msg

    # Append persona context (if present)
    if hasattr(request, "context") and isinstance(request.context, dict) and request.context.get("personas"):
        user_msg += "\n\nTarget Personas:\n" + json.dumps(request.context["personas"], indent=2)

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]

    output: Dict[str, Any] = _MOCK_OUTPUT
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": "Bearer %s" % settings.OPENROUTER_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "response_format": {"type": "json_object"},
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)

                try:
                    output = json.loads(content)
                    output["type"] = "creative"
                except json.JSONDecodeError:
                    output = {"type": "creative", "raw_response": content}
            else:
                log.warning("Creative Agent: OpenRouter returned %d", resp.status_code)
    except Exception as e:
        log.warning("Creative Agent error: %s", e)

    # cost: Claude Sonnet ~$3/M input, $15/M output
    cost = (prompt_tokens * 3 + completion_tokens * 15) / 1_000_000

    return {
        "output": output,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "estimated_cost_usd": cost,
    }
