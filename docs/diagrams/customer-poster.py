"""
ReceptivIQ — Customer-Facing Architecture Poster (hand-crafted SVG)

Why hand-crafted SVG instead of diagrams library:
- Pixel-perfect control: every label position, font size, and spacing
  is explicit. No graphviz auto-layout surprises.
- No text overflow / clipping
- Generates a self-contained SVG (icons base64-embedded) — portable

Output: customer-poster.png + customer-poster.svg
"""
from __future__ import annotations
import base64
import os
import subprocess
from pathlib import Path

ICONS_DIR = Path("icons")
OUT_SVG = Path("customer-poster.svg")
OUT_PNG = Path("customer-poster.png")


def img_b64(name: str) -> str:
    """Load an icon PNG and return data URI for inline SVG embedding."""
    p = ICONS_DIR / f"{name}.png"
    if not p.exists():
        raise FileNotFoundError(p)
    data = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


# ═════════════ Theme tokens ═════════════
BG          = "#0B1220"
TITLE       = "#F8FAFC"
SUBTITLE    = "#94A3B8"
CARD_BG     = "#101a30"
CARD_STROKE = "#1E293B"

TIER1_ACCENT = "#F59E0B"   # amber
TIER2_ACCENT = "#A855F7"   # purple
TIER3_ACCENT = "#EC4899"   # pink
TIER4_ACCENT = "#10B981"   # emerald

LABEL       = "#E2E8F0"
CAPTION     = "#94A3B8"
ARROW       = "#475569"

W, H = 1800, 1180
PAD_X = 70

# Tier Y-positions (top of each band)
T1_Y, T1_H = 110, 220
T2_Y, T2_H = 360, 220
T3_Y, T3_H = 610, 220
T4_Y, T4_H = 860, 240


def tier_band(y: int, h: int, accent: str, number: str, title: str, subtitle: str) -> str:
    """Render the rounded-rect band, top-left number badge, and titles for a tier."""
    band = f"""
    <rect x="{PAD_X-10}" y="{y}" width="{W-2*(PAD_X-10)}" height="{h}"
          fill="{CARD_BG}" stroke="{accent}" stroke-width="2.5"
          rx="20" ry="20" opacity="0.92" />
    <!-- Number badge -->
    <circle cx="{PAD_X+20}" cy="{y+30}" r="22" fill="{accent}" />
    <text x="{PAD_X+20}" y="{y+38}" font-family="Helvetica, Arial, sans-serif"
          font-size="24" font-weight="700" fill="#0B1220"
          text-anchor="middle">{number}</text>
    <!-- Title -->
    <text x="{PAD_X+55}" y="{y+24}" font-family="Helvetica, Arial, sans-serif"
          font-size="22" font-weight="700" fill="{accent}">{title}</text>
    <text x="{PAD_X+55}" y="{y+48}" font-family="Helvetica, Arial, sans-serif"
          font-size="14" font-weight="400" fill="{SUBTITLE}">{subtitle}</text>
    """
    return band


def icon_card(x: int, y: int, slug: str, label: str, w: int = 100, h: int = 130) -> str:
    """Icon centered above a small label. Used for data sources & deliverables."""
    icon_size = 72
    icon_x = x + (w - icon_size) // 2
    icon_y = y
    text_y = y + icon_size + 22
    return f"""
    <image href="{img_b64(slug)}" x="{icon_x}" y="{icon_y}"
           width="{icon_size}" height="{icon_size}" />
    <text x="{x + w//2}" y="{text_y}" font-family="Helvetica, Arial, sans-serif"
          font-size="13" font-weight="600" fill="{LABEL}"
          text-anchor="middle">{label}</text>
    """


def big_card(x: int, y: int, slug: str, title: str, caption: str,
             w: int = 240, h: int = 140) -> str:
    """Larger card with icon + bold title + caption — for Pipeline and AI tiers."""
    icon_size = 64
    return f"""
    <rect x="{x}" y="{y}" width="{w}" height="{h}"
          fill="#13203a" stroke="{CARD_STROKE}" stroke-width="1.2"
          rx="14" ry="14" />
    <image href="{img_b64(slug)}" x="{x + 18}" y="{y + (h - icon_size)//2}"
           width="{icon_size}" height="{icon_size}" />
    <text x="{x + 100}" y="{y + 50}" font-family="Helvetica, Arial, sans-serif"
          font-size="17" font-weight="700" fill="{LABEL}">{title}</text>
    <text x="{x + 100}" y="{y + 75}" font-family="Helvetica, Arial, sans-serif"
          font-size="12" fill="{CAPTION}">{caption.splitlines()[0] if caption else ''}</text>
    <text x="{x + 100}" y="{y + 92}" font-family="Helvetica, Arial, sans-serif"
          font-size="12" fill="{CAPTION}">{(caption.splitlines() + [''])[1] if caption else ''}</text>
    <text x="{x + 100}" y="{y + 109}" font-family="Helvetica, Arial, sans-serif"
          font-size="12" fill="{CAPTION}">{(caption.splitlines() + ['',''])[2] if caption else ''}</text>
    """


def arrow_right(x1: int, y1: int, x2: int, y2: int) -> str:
    """Horizontal arrow between cards."""
    return f"""
    <path d="M {x1} {y1} L {x2-8} {y2}"
          stroke="{ARROW}" stroke-width="2.5" fill="none"
          marker-end="url(#arrow)" />
    """


def arrow_down(x: int, y1: int, y2: int) -> str:
    return f"""
    <path d="M {x} {y1} L {x} {y2-8}"
          stroke="{ARROW}" stroke-width="2.5" fill="none"
          marker-end="url(#arrow)" />
    """


# ═════════════ Build the SVG ═════════════

# Tier 1: 9 data sources, evenly distributed
T1_LOGOS = [
    ("ga4",         "Google Analytics 4"),
    ("meta",        "Meta Ads"),
    ("hubspot",     "HubSpot"),
    ("tiktok",      "TikTok Ads"),
    ("dv360",       "DV360"),
    ("trade_desk",  "Trade Desk"),
    ("salesforce",  "Salesforce"),
    ("liveramp",    "LiveRamp"),
    ("plus_more",   "+ 8 more"),
]

# Tier 2: Pipeline (4 steps)
T2_STEPS = [
    ("compliance",     "Compliance Gate",  "HIPAA / GDPR / CCPA\nPHI scan · anonymize PII\nUnconditional, no bypass"),
    ("apacheairflow",  "Airflow",          "Automated daily sync\nfrom all data sources"),
    ("snowflake",      "Snowflake",        "Your private cloud\nwarehouse\n(DuckDB in dev)"),
    ("openrouter",     "dbt",              "Smart transformations\ninside the warehouse\n(ELT pattern)"),
]
# Use a real dbt visual by swapping the openrouter placeholder
# We have the dbt brand from diagrams library but here we need an image file.
# Falls back to openrouter visually if dbt PNG isn't generated.
if (ICONS_DIR / "dbt.png").exists():
    T2_STEPS[3] = ("dbt", "dbt", T2_STEPS[3][2])

# Tier 3: AI Agents
T3_AGENTS = [
    ("personas",      "Persona Agent",      "AI-generated\naudience personas from\ncross-platform behavior"),
    ("creatives",     "Creative Agent",     "Multi-platform ad copy\naligned to your\nbrand voice"),
    ("attribution",   "Attribution Agent",  "Multi-touch ROI\nacross GA4 &amp; Meta\n&amp; HubSpot &amp; more"),
    ("anthropic",     "Claude (Anthropic)", "Powered by Opus 4.7\nvia OpenRouter\n(Bedrock for HIPAA)"),
]

# Tier 4: Deliverables
T4_OUTS = [
    ("dashboard",    "Real-time Dashboards"),
    ("portal",       "White-label Portal"),
    ("pdf_report",   "Scheduled PDF Reports"),
    ("audience",     "Audience Exports"),
    ("email_alert",  "Budget &amp; Pacing Alerts"),
]


def main() -> None:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}"'
        f' style="background:{BG}">',
        f'<rect width="{W}" height="{H}" fill="{BG}" />',
        # Arrow marker
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"'
        '   markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'  <path d="M 0 0 L 10 5 L 0 10 z" fill="{ARROW}"/></marker></defs>',

        # ═══ Title ═══
        f'<text x="{W//2}" y="60" font-family="Helvetica, Arial, sans-serif"'
        f' font-size="34" font-weight="700" fill="{TITLE}" text-anchor="middle">'
        f'ReceptivIQ Platform</text>',
        f'<text x="{W//2}" y="88" font-family="Helvetica, Arial, sans-serif"'
        f' font-size="16" fill="{SUBTITLE}" text-anchor="middle">'
        f'Your AI-Native Marketing Operating System &#8212; '
        f'unify 17+ data sources, generate insights with Claude, deliver to clients</text>',
    ]

    # ─── Tier 1 ───
    parts.append(tier_band(T1_Y, T1_H, TIER1_ACCENT, "1",
                           "YOUR MARKETING DATA SOURCES",
                           "We unify what you already use — automatic OAuth / API-Key onboarding"))
    n = len(T1_LOGOS)
    avail = W - 2 * PAD_X - 20
    col_w = avail // n
    icon_y = T1_Y + 80
    for i, (slug, label) in enumerate(T1_LOGOS):
        cx = PAD_X + 10 + i * col_w + col_w // 2 - 50
        parts.append(icon_card(cx, icon_y, slug, label))

    # ─── Tier 2 ───
    parts.append(tier_band(T2_Y, T2_H, TIER2_ACCENT, "2",
                           "SECURE DATA PIPELINE",
                           "Compliant by design — every record passes the gate before reaching the warehouse"))
    card_w = 360
    n2 = len(T2_STEPS)
    gap = (W - 2*PAD_X - n2 * card_w) // (n2 - 1)
    base_y = T2_Y + 70
    for i, (slug, title, caption) in enumerate(T2_STEPS):
        x = PAD_X + i * (card_w + gap)
        parts.append(big_card(x, base_y, slug, title, caption, w=card_w))
        # arrow between cards
        if i < n2 - 1:
            ax1 = x + card_w
            ax2 = x + card_w + gap
            ay = base_y + 70
            parts.append(arrow_right(ax1, ay, ax2, ay))

    # ─── Tier 3 ───
    parts.append(tier_band(T3_Y, T3_H, TIER3_ACCENT, "3",
                           "AI BRAIN — three specialist agents",
                           "Each agent reasons over the unified dataset; Claude (Opus 4.7) provides the foundation model"))
    card_w3 = 360
    n3 = len(T3_AGENTS)
    gap3 = (W - 2*PAD_X - n3 * card_w3) // (n3 - 1)
    base_y3 = T3_Y + 70
    for i, (slug, title, caption) in enumerate(T3_AGENTS):
        x = PAD_X + i * (card_w3 + gap3)
        parts.append(big_card(x, base_y3, slug, title, caption, w=card_w3))

    # ─── Tier 4 ───
    parts.append(tier_band(T4_Y, T4_H, TIER4_ACCENT, "4",
                           "DELIVERED TO YOUR TEAM &amp; CLIENTS",
                           "White-labeled, real-time — agency staff use the Ops Console; brand clients use the Portal."))
    n4 = len(T4_OUTS)
    col_w4 = (W - 2*PAD_X) // n4
    icon_y4 = T4_Y + 90
    for i, (slug, label) in enumerate(T4_OUTS):
        cx = PAD_X + i * col_w4 + col_w4 // 2 - 50
        parts.append(icon_card(cx, icon_y4, slug, label, w=100, h=130))

    # ─── Vertical flow arrows between tiers ───
    parts.append(arrow_down(W//2, T1_Y + T1_H + 8, T2_Y - 4))
    parts.append(arrow_down(W//2, T2_Y + T2_H + 8, T3_Y - 4))
    parts.append(arrow_down(W//2, T3_Y + T3_H + 8, T4_Y - 4))

    # ─── Footer credits ───
    parts.append(
        f'<text x="{W//2}" y="{H-22}" font-family="Helvetica, Arial, sans-serif"'
        f' font-size="11" fill="{SUBTITLE}" text-anchor="middle">'
        f'GDPR · CCPA · HIPAA  compliant by design   ·   '
        f'17+ platforms unified   ·   Powered by Anthropic Claude</text>'
    )

    parts.append('</svg>')

    OUT_SVG.write_text("\n".join(parts), encoding="utf-8")
    print(f"✓ wrote {OUT_SVG} ({OUT_SVG.stat().st_size // 1024} KB)")

    # Convert SVG → PNG
    subprocess.run(
        ["rsvg-convert", "-w", str(W), "-h", str(H),
         str(OUT_SVG), "-o", str(OUT_PNG)],
        check=True,
    )
    print(f"✓ wrote {OUT_PNG} ({OUT_PNG.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
