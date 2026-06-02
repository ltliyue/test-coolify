"""
ReceptivIQ — Layered Stack Architecture (Development Environment) — English

Design intent:
- Strict top-down 7-layer architecture: Presentation → Infrastructure
- Each layer = a horizontal band with Layer N label on the left, tool nodes on the right
- LangChain is used for agent orchestration alongside httpx for direct calls
- Coolify as PaaS control plane at the bottom, dashed boundary covers all Docker services
- 5-color data flow arrows: User / AI / Data / Compliance / Deploy

Output: dev-stack-layered-en.{svg, png}
"""
from __future__ import annotations
import base64
import subprocess
from pathlib import Path

ICONS_DIR = Path("icons")
OUT_SVG = Path("dev-stack-layered-en.svg")
OUT_PNG = Path("dev-stack-layered-en.png")


# ───────── Theme ─────────
BG          = "#0B1220"
NODE_BG     = "#13203a"
TITLE       = "#F8FAFC"
SUBTITLE    = "#94A3B8"
LABEL       = "#E2E8F0"
DIM_LABEL   = "#94A3B8"
STROKE      = "#1E293B"

# Data flow colors
EDGE_USER   = "#06B6D4"   # cyan — user traffic
EDGE_AI     = "#EC4899"   # pink — LLM calls
EDGE_DATA   = "#10B981"   # emerald — ETL/data ingest
EDGE_GUARD  = "#A855F7"   # purple — compliance/audit
EDGE_DEPLOY = "#F59E0B"   # amber — deploy/management

# Layer accent colors
LAYER_COLORS = {
    1: "#06B6D4",   # Presentation — cyan
    2: "#3B82F6",   # API Gateway — blue
    3: "#EC4899",   # Application — pink
    4: "#10B981",   # Transformation — emerald
    5: "#8B5CF6",   # Data Storage — violet
    6: "#F59E0B",   # External — amber
    7: "#EF4444",   # Infrastructure — red
}

# Canvas dimensions
W, H = 2320, 1500
CR = 1960       # Original content right boundary (preserve existing layout)
PAD = 40
LAYER_LABEL_W = 180

# Y coords + heights for each of the 7 layer bands
BAND_TOP = 130
BAND_GAP = 8
BAND_HEIGHTS = {
    1: 130,   # Presentation
    2: 150,   # API Gateway
    3: 200,   # Service Layer
    4: 220,   # Transformation
    5: 170,   # Data Storage
    6: 200,   # External
    7: 170,   # Infrastructure
}


def img_b64(name: str) -> str:
    p = ICONS_DIR / f"{name}.png"
    if not p.exists():
        return ""
    return f"data:image/png;base64,{base64.b64encode(p.read_bytes()).decode('ascii')}"


def band_y(layer: int) -> int:
    """Returns top Y coordinate for a given layer's band"""
    y = BAND_TOP
    for i in range(1, layer):
        y += BAND_HEIGHTS[i] + BAND_GAP
    return y


def layer_label(layer: int, name: str, subtitle: str, description: str) -> str:
    """Left-side layer label card"""
    y_top = band_y(layer)
    h = BAND_HEIGHTS[layer]
    cx = PAD + LAYER_LABEL_W // 2
    cy = y_top + h // 2
    color = LAYER_COLORS[layer]
    return f"""
  <g>
    <rect x="{PAD}" y="{y_top}" width="{LAYER_LABEL_W}" height="{h}"
          fill="{NODE_BG}" stroke="{color}" stroke-width="2" rx="14"/>
    <rect x="{PAD}" y="{y_top}" width="6" height="{h}" fill="{color}" rx="3"/>
    <text x="{cx}" y="{cy - 28}" font-family="Helvetica" font-size="13"
          font-weight="700" fill="{color}" text-anchor="middle">LAYER {layer}</text>
    <text x="{cx}" y="{cy - 4}" font-family="Helvetica" font-size="17"
          font-weight="800" fill="{TITLE}" text-anchor="middle">{name}</text>
    <text x="{cx}" y="{cy + 18}" font-family="Helvetica" font-size="11"
          fill="{DIM_LABEL}" text-anchor="middle">{subtitle}</text>
    <text x="{cx}" y="{cy + 38}" font-family="Helvetica" font-size="10"
          fill="{DIM_LABEL}" text-anchor="middle" font-style="italic">{description}</text>
  </g>"""


def band_bg(layer: int) -> str:
    """Layer band background (gradient + rounded corners)"""
    y_top = band_y(layer)
    h = BAND_HEIGHTS[layer]
    color = LAYER_COLORS[layer]
    x = PAD + LAYER_LABEL_W + 20
    band_w = CR - x
    grad_id = f"grad-layer-{layer}"
    return f"""
  <defs>
    <linearGradient id="{grad_id}" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{color}" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="{color}" stop-opacity="0.02"/>
    </linearGradient>
  </defs>
  <rect x="{x}" y="{y_top}" width="{band_w}" height="{h}"
        fill="url(#{grad_id})" stroke="{color}" stroke-width="1" stroke-opacity="0.3" rx="12"/>"""


def tool_node(x: int, y: int, slug: str, name: str, role: str = "",
              w: int = 160, h: int = 110, accent: str = "#475569") -> str:
    """Tool node: icon + name + role description.
    Adaptive: switches to horizontal layout for short boxes (h<70)."""
    out = [
        f'<g>',
        f'  <rect x="{x+3}" y="{y+3}" width="{w}" height="{h}" fill="#000" opacity="0.25" rx="10"/>',
        f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{NODE_BG}"'
        f' stroke="{accent}" stroke-width="1.5" rx="10"/>',
        f'  <rect x="{x}" y="{y}" width="{w}" height="3" fill="{accent}" rx="1"/>',
    ]
    icon_b64 = img_b64(slug)

    if h < 70:
        # Horizontal layout: icon on LEFT, text on RIGHT
        icon_size = h - 18  # leaves 9px padding top and bottom
        icon_x = x + 8
        icon_y = y + (h - icon_size) // 2 + 1
        text_x = icon_x + icon_size + 8
        if icon_b64:
            out.append(
                f'  <image href="{icon_b64}" x="{icon_x}" y="{icon_y}"'
                f' width="{icon_size}" height="{icon_size}"/>'
            )
        if role:
            out.append(
                f'  <text x="{text_x}" y="{y + h//2 - 2}" font-family="Helvetica"'
                f' font-size="12" font-weight="700" fill="{LABEL}">{name}</text>'
            )
            out.append(
                f'  <text x="{text_x}" y="{y + h//2 + 12}" font-family="Helvetica"'
                f' font-size="9" fill="{DIM_LABEL}">{role}</text>'
            )
        else:
            out.append(
                f'  <text x="{text_x}" y="{y + h//2 + 4}" font-family="Helvetica"'
                f' font-size="12" font-weight="700" fill="{LABEL}">{name}</text>'
            )
    else:
        # Vertical layout (original): icon centered top, text below
        icon_size = 48 if h >= 100 else 40
        icon_y = y + 12
        text_y = y + h - 30 if role else y + h - 14
        role_y = y + h - 12
        if icon_b64:
            out.append(
                f'  <image href="{icon_b64}" x="{x + (w-icon_size)//2}" y="{icon_y}"'
                f' width="{icon_size}" height="{icon_size}"/>'
            )
        else:
            out.append(
                f'  <rect x="{x + (w-icon_size)//2}" y="{icon_y}" width="{icon_size}" height="{icon_size}"'
                f' fill="{accent}" opacity="0.3" rx="6"/>'
            )
        out.append(
            f'  <text x="{x + w//2}" y="{text_y}" font-family="Helvetica" font-size="12"'
            f' font-weight="700" fill="{LABEL}" text-anchor="middle">{name}</text>'
        )
        if role:
            out.append(
                f'  <text x="{x + w//2}" y="{role_y}" font-family="Helvetica"'
                f' font-size="9" fill="{DIM_LABEL}" text-anchor="middle">{role}</text>'
            )
    out.append('</g>')
    return "\n".join(out)


def small_chip(x: int, y: int, slug: str, name: str,
               w: int = 100, h: int = 78, accent: str = "#475569") -> str:
    """Compact chip node: for data sources, agents, and other multi-item groups.
    Auto-scales icon size based on chip height."""
    # Adaptive icon size: bigger chips get bigger icons
    icon = 40 if h >= 72 else 32
    icon_top = y + 8
    text_y = y + h - 8  # 8px from bottom for text baseline
    out = [
        f'<g>',
        f'  <rect x="{x+2}" y="{y+2}" width="{w}" height="{h}" fill="#000" opacity="0.2" rx="8"/>',
        f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{NODE_BG}"'
        f' stroke="{accent}" stroke-width="1" rx="8"/>',
    ]
    icon_b64 = img_b64(slug)
    if icon_b64:
        out.append(
            f'  <image href="{icon_b64}" x="{x + (w-icon)//2}" y="{icon_top}"'
            f' width="{icon}" height="{icon}"/>'
        )
    out.append(
        f'  <text x="{x + w//2}" y="{text_y}" font-family="Helvetica" font-size="10"'
        f' font-weight="600" fill="{LABEL}" text-anchor="middle">{name}</text>'
    )
    out.append('</g>')
    return "\n".join(out)


def section_title(x: int, y: int, text: str, color: str) -> str:
    """Sub-group title within a band"""
    return (f'<text x="{x}" y="{y}" font-family="Helvetica" font-size="11"'
            f' font-weight="700" fill="{color}" letter-spacing="1.5">{text}</text>')


def arrow_down(x: int, y_top: int, y_bot: int, color: str, label: str = "",
               width: float = 2.2, dashed: bool = False) -> str:
    """Vertical downward arrow"""
    dash = ' stroke-dasharray="6 4"' if dashed else ''
    out = [
        f'<path d="M {x} {y_top} L {x} {y_bot}" stroke="{color}"'
        f' stroke-width="{width}" fill="none"{dash} marker-end="url(#arrow-{color[1:]})"/>'
    ]
    if label:
        ly = (y_top + y_bot) // 2
        text_w = len(label) * 6 + 12
        out.append(
            f'<rect x="{x - text_w//2}" y="{ly - 10}" width="{text_w}" height="16"'
            f' fill="{BG}" stroke="{color}" stroke-width="1" rx="8"/>'
        )
        out.append(
            f'<text x="{x}" y="{ly + 2}" font-family="Helvetica" font-size="10"'
            f' font-weight="700" fill="{color}" text-anchor="middle">{label}</text>'
        )
    return "\n".join(out)




# ─────────── v2 differentiation helpers ───────────
def env_badge(x: int, y: int, label: str, sub: str, color: str) -> str:
    """Big environment badge in top-right corner."""
    w, h = 220, 64
    return f"""
  <g>
    <rect x="{x+4}" y="{y+4}" width="{w}" height="{h}" fill="{color}" opacity="0.25" rx="10"/>
    <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" opacity="0.18" rx="10"/>
    <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{color}" stroke-width="3" rx="10"/>
    <text x="{x + w//2}" y="{y + 36}" font-family="Helvetica" font-size="26"
          font-weight="900" fill="{color}" text-anchor="middle" letter-spacing="3">{label}</text>
    <text x="{x + w//2}" y="{y + 54}" font-family="Helvetica" font-size="10"
          font-weight="600" fill="{color}" text-anchor="middle" opacity="0.9">{sub}</text>
  </g>"""


def watermark(text: str, color: str) -> str:
    """Huge faint diagonal watermark behind everything."""
    return (
        f'<text x="{(CR+PAD)//2}" y="{H//2 + 80}" font-family="Helvetica" font-size="320"'
        f' font-weight="900" fill="{color}" opacity="0.05" text-anchor="middle"'
        f' transform="rotate(-22 {W//2} {H//2})" letter-spacing="20">{text}</text>'
    )


def tool_tag(x: int, y: int, label: str, color: str) -> str:
    """Small pill tag for tool quality indicator."""
    w = len(label) * 6 + 14
    return (
        f'<g>'
        f'<rect x="{x}" y="{y}" width="{w}" height="15" fill="{color}" opacity="0.22" rx="7"/>'
        f'<rect x="{x}" y="{y}" width="{w}" height="15" fill="none" stroke="{color}"'
        f' stroke-width="1" rx="7"/>'
        f'<text x="{x + w//2}" y="{y + 11}" font-family="Helvetica" font-size="9"'
        f' font-weight="700" fill="{color}" text-anchor="middle">{label}</text>'
        f'</g>'
    )


# ════════════════════════ Begin SVG ════════════════════════
parts: list[str] = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Helvetica, Arial, sans-serif">',
    '<defs>',
    f'  <linearGradient id="bg-grad" x1="0%" y1="0%" x2="0%" y2="100%">',
    f'    <stop offset="0%" stop-color="#0F172A"/>',
    f'    <stop offset="100%" stop-color="#020617"/>',
    f'  </linearGradient>',
]

arrow_colors = [EDGE_USER, EDGE_AI, EDGE_DATA, EDGE_GUARD, EDGE_DEPLOY, DIM_LABEL,
                LAYER_COLORS[1], LAYER_COLORS[2], LAYER_COLORS[3], LAYER_COLORS[4],
                LAYER_COLORS[5], LAYER_COLORS[6], LAYER_COLORS[7]]
for c in arrow_colors:
    cid = c[1:]
    parts.append(
        f'  <marker id="arrow-{cid}" viewBox="0 0 10 10" refX="9" refY="5"'
        f' markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f' <path d="M 0 0 L 10 5 L 0 10 z" fill="{c}"/></marker>'
    )
parts.append('</defs>')
parts.append(f'<rect width="{W}" height="{H}" fill="url(#bg-grad)"/>')
parts.append(watermark('DEV', '#F59E0B'))

# ─────────────── Title ───────────────
parts.append(
    f'<text x="{(CR+PAD)//2}" y="50" font-family="Helvetica" font-size="34"'
    f' font-weight="800" fill="{TITLE}" text-anchor="middle">'
    f'ReceptivIQ Platform &#8212; Development Stack Architecture</text>'
)
parts.append(
    f'<text x="{(CR+PAD)//2}" y="80" font-family="Helvetica" font-size="14"'
    f' fill="{SUBTITLE}" text-anchor="middle">'
    f'7-layer development stack  &#183;  Coolify-managed deployment  &#183;  '
    f'compliance-first data flow</text>'
)
parts.append(
    f'<text x="{(CR+PAD)//2}" y="102" font-family="Helvetica" font-size="11"'
    f' fill="{DIM_LABEL}" text-anchor="middle" font-style="italic">'
    f'Deployment: Coolify (graphical PaaS)  |  '
    f'Backend: Python/FastAPI  |  Frontend: React  |  '
    f'Storage: PostgreSQL 3-Lake (Landing + Raw PII + Processed · local schema simulation)'
)
parts.append('</text>')
parts.append(env_badge(CR - 220, 28, '⚠ DEV', 'DEVELOPMENT ENV', '#F59E0B'))

# ═══════════════════════════════════════════════════════════
# LAYER 1 — Presentation
# ═══════════════════════════════════════════════════════════
parts.append(band_bg(1))
parts.append(layer_label(1, "Presentation", "Frontend SPA", "User-Facing Apps"))

L1_Y = band_y(1) + 12
L1_X0 = PAD + LAYER_LABEL_W + 60
parts.append(tool_node(L1_X0,       L1_Y, "react",   "React",         "UI Framework + TypeScript", accent=LAYER_COLORS[1]))
parts.append(tool_node(L1_X0 + 180, L1_Y, "google",  "Google OAuth",  "Authentication 2.0",       accent=LAYER_COLORS[1]))

parts.append(
    f'<text x="{CR - 280}" y="{L1_Y + 20}" font-family="Helvetica" font-size="11"'
    f' font-weight="700" fill="{LAYER_COLORS[1]}">USER TYPES</text>'
)
parts.append(small_chip(CR - 280, L1_Y + 32, "agent_svc", "Staff",        accent=LAYER_COLORS[1]))
parts.append(small_chip(CR - 180, L1_Y + 32, "client",    "Client",       accent=LAYER_COLORS[1]))
parts.append(small_chip(CR - 80,  L1_Y + 32, "auth",      "Admin",        accent=LAYER_COLORS[1]))

# ═══════════════════════════════════════════════════════════
# LAYER 2 — API Gateway
# ═══════════════════════════════════════════════════════════
parts.append(band_bg(2))
parts.append(layer_label(2, "API Gateway", "HTTP / WebSocket", "Routing + Middleware"))

L2_Y = band_y(2) + 18
L2_X0 = PAD + LAYER_LABEL_W + 60
parts.append(tool_node(L2_X0,       L2_Y, "fastapi",  "FastAPI",       "async REST + WS",          accent=LAYER_COLORS[2]))
parts.append(tool_node(L2_X0 + 180, L2_Y, "ws",       "WebSocket",     "Real-time /ws",               accent=LAYER_COLORS[2]))

MID_X = L2_X0 + 360
parts.append(section_title(MID_X, L2_Y + 12, "MIDDLEWARE CHAIN", LAYER_COLORS[2]))
mid_items = [
    ("CORS", "API access control"),
    ("Security Headers", "X-Frame, HSTS, CSP"),
    ("HIPAA SessionGuard", "15-min PHI timeout"),
    ("Request Logging", "request_id injection"),
]
for i, (name, role) in enumerate(mid_items):
    chip_x = MID_X + (i % 2) * 200
    chip_y = L2_Y + 20 + (i // 2) * 50
    parts.append(
        f'<rect x="{chip_x}" y="{chip_y}" width="190" height="40" fill="{NODE_BG}"'
        f' stroke="{LAYER_COLORS[2]}" stroke-width="1" rx="6"/>'
    )
    parts.append(
        f'<text x="{chip_x + 12}" y="{chip_y + 17}" font-family="Helvetica"'
        f' font-size="11" font-weight="700" fill="{LABEL}">{name}</text>'
    )
    parts.append(
        f'<text x="{chip_x + 12}" y="{chip_y + 32}" font-family="Helvetica"'
        f' font-size="9" fill="{DIM_LABEL}">{role}</text>'
    )

# ═══════════════════════════════════════════════════════════
# LAYER 3 — Application / Service
# ═══════════════════════════════════════════════════════════
parts.append(band_bg(3))
parts.append(layer_label(3, "Application", "Service Layer", "AI + Business Logic"))

L3_Y = band_y(3) + 12
L3_X0 = PAD + LAYER_LABEL_W + 60

parts.append(tool_node(L3_X0, L3_Y, "brain", "AI Brain", "LLM router + budget", accent=LAYER_COLORS[3], h=140))

AGENT_X = L3_X0 + 200
parts.append(section_title(AGENT_X, L3_Y + 8, "AI AGENTS", LAYER_COLORS[3]))
parts.append(small_chip(AGENT_X,        L3_Y + 16, "persona",    "Persona",     accent=LAYER_COLORS[3]))
parts.append(small_chip(AGENT_X + 105,  L3_Y + 16, "creatives",  "Creative",    accent=LAYER_COLORS[3]))
parts.append(small_chip(AGENT_X + 210,  L3_Y + 16, "attribution","Attribution", accent=LAYER_COLORS[3]))

parts.append(
    f'<rect x="{AGENT_X}" y="{L3_Y + 100}" width="315" height="36" fill="{NODE_BG}"'
    f' stroke="{EDGE_AI}" stroke-width="1.5" rx="6"/>'
)
parts.append(
    f'<text x="{AGENT_X + 12}" y="{L3_Y + 118}" font-family="Helvetica"'
    f' font-size="11" font-weight="700" fill="{EDGE_AI}">LangChain &#8594; OpenRouter</text>'
)
parts.append(
    f'<text x="{AGENT_X + 12}" y="{L3_Y + 130}" font-family="Helvetica"'
    f' font-size="9" fill="{DIM_LABEL}">Agent orchestration &#183; structured tool calls</text>'
)

parts.append(tool_node(L3_X0 + 540, L3_Y, "langfuse", "Langfuse SDK", "LLM tracing", accent=EDGE_AI, h=140))

BIZ_X = L3_X0 + 720
parts.append(section_title(BIZ_X, L3_Y + 8, "BUSINESS SERVICES", LAYER_COLORS[3]))
biz_items = [
    ("dashboard",     "Reports"),
    ("audience",      "Audience\nExport"),
    ("biz_svc",       "Campaign"),
    ("compliance",    "Budget\nPacing"),
    ("agent_svc",     "Notifs"),
    ("biz_svc",       "Brand"),
    ("biz_svc",       "Field\nMapping"),
    ("auth",          "OAuth"),
    ("agent_svc",     "Platform\nReg"),
]
for i, (slug, name) in enumerate(biz_items):
    chip_x = BIZ_X + (i % 5) * 95
    chip_y = L3_Y + 16 + (i // 5) * 78
    parts.append(small_chip(chip_x, chip_y, slug, name, accent=LAYER_COLORS[3], w=90, h=72))

# ═══════════════════════════════════════════════════════════
# LAYER 4 — Transformation / ELT
# ═══════════════════════════════════════════════════════════
parts.append(band_bg(4))
parts.append(layer_label(4, "ELT Pipeline", "Extract-Load-Transform", "Save first, then transform"))

L4_Y = band_y(4) + 12
L4_X0 = PAD + LAYER_LABEL_W + 60

parts.append(section_title(L4_X0, L4_Y + 4, "ORCHESTRATION", LAYER_COLORS[4]))
# Orchestrator choice: Airflow (current) / Dagster (target, per ADR-003)
parts.append(tool_node(L4_X0,        L4_Y + 14, "apacheairflow", "Airflow",   "ELT DAG · current",   accent=LAYER_COLORS[4], h=130, w=120))
parts.append(
    f'<rect x="{L4_X0 + 124}" y="{L4_Y + 14 + 50}" width="28" height="30"'
    f' fill="{NODE_BG}" stroke="{LAYER_COLORS[4]}" stroke-width="1.2" rx="6"/>'
    f'<text x="{L4_X0 + 138}" y="{L4_Y + 14 + 70}" font-family="Helvetica" font-size="10"'
    f' font-weight="800" fill="{LAYER_COLORS[4]}" text-anchor="middle">OR</text>'
)
parts.append(tool_node(L4_X0 + 156,  L4_Y + 14, "dagster",      "Dagster",     "Asset · target",      accent=LAYER_COLORS[4], h=130, w=120))
parts.append(tool_node(L4_X0 + 286,  L4_Y + 14, "celery",       "Celery",      "Async tasks",         accent=LAYER_COLORS[4], h=130, w=130))

ETL_X = L4_X0 + 430
parts.append(section_title(ETL_X, L4_Y + 4, "EXTRACT ADAPTERS", LAYER_COLORS[4]))
adapters = [
    ("ga4",      "GA4"),
    ("meta",     "Meta"),
    ("hubspot",  "HubSpot"),
    ("dv360",    "DV360"),
    ("stackadapt", "StackAdpt"),
    ("leadrx",   "LeadRX"),
    ("liveramp", "LiveRamp"),
    ("quorum",   "Quorum"),
    ("tiktok",   "TikTok"),
    ("plus_more", "+more"),
]
for i, (slug, name) in enumerate(adapters):
    chip_x = ETL_X + (i % 5) * 86
    chip_y = L4_Y + 14 + (i // 5) * 66
    parts.append(small_chip(chip_x, chip_y, slug, name, accent=LAYER_COLORS[4], w=82, h=62))

# Compliance moved to outer wrap at end of file

DBT_Y = L4_Y + 150
parts.append(
    f'<rect x="{L4_X0 - 4}" y="{DBT_Y - 14}" width="240" height="20" fill="{BG}"'
    f' stroke="{LAYER_COLORS[4]}" stroke-width="1" rx="6"/>'
    f'<text x="{L4_X0 + 116}" y="{DBT_Y + 1}" font-family="Helvetica" font-size="11"'
    f' font-weight="700" fill="{LAYER_COLORS[4]}" text-anchor="middle"'
    f' letter-spacing="1">TRANSFORM (dbt SQL pipeline)</text>'
)
parts.append(tool_node(L4_X0, DBT_Y + 10, "dbt", "dbt Core", "Clean · Merge · Map · Aggregate", accent=LAYER_COLORS[4], h=55, w=160))
dbt_layers = [
    ("staging",   "Clean",     "standardize fields"),
    ("canonical", "Merge",     "unify cross-platform"),
    ("map",       "Map",       "fields → entities"),
    ("marts",     "Aggregate", "business reports"),
]
for i, (slug, name, hint) in enumerate(dbt_layers):
    bx = L4_X0 + 180 + i * 160
    parts.append(
        f'<rect x="{bx}" y="{DBT_Y + 10}" width="140" height="55" fill="{NODE_BG}"'
        f' stroke="{LAYER_COLORS[4]}" stroke-width="1" rx="8"/>'
    )
    icon_b64 = img_b64(slug)
    if icon_b64:
        parts.append(
            f'<image href="{icon_b64}" x="{bx + 6}" y="{DBT_Y + 19}"'
            f' width="36" height="36"/>'
        )
    parts.append(
        f'<text x="{bx + 48}" y="{DBT_Y + 32}" font-family="Helvetica" font-size="14"'
        f' font-weight="800" fill="{LABEL}">{name}</text>'
    )
    parts.append(
        f'<text x="{bx + 48}" y="{DBT_Y + 47}" font-family="Helvetica" font-size="9"'
        f' fill="{DIM_LABEL}">{hint}</text>'
    )
    if i < 3:
        parts.append(
            f'<path d="M {bx + 142} {DBT_Y + 38} L {bx + 158} {DBT_Y + 38}"'
            f' stroke="{LAYER_COLORS[4]}" stroke-width="2" marker-end="url(#arrow-{LAYER_COLORS[4][1:]})"/>'
        )

# ═══════════════════════════════════════════════════════════
# LAYER 5 — Data Storage
# ═══════════════════════════════════════════════════════════
parts.append(band_bg(5))
parts.append(layer_label(5, "Data Storage", "OLTP + OLAP + Cache", "Persistence Tier"))

L5_Y = band_y(5) + 25
L5_X0 = PAD + LAYER_LABEL_W + 60

# ── L5 redesign: 3-Lake (dev: local PG schema simulation) + Redis + MinIO ──
EDGE_PII_LOCAL = "#EF4444"
BRONZE_LOCAL = "#A16207"
NODE_W = 130

# 🟫 Landing Lake (Bronze · dev = postgres schema `landing`)
parts.append(tool_node(L5_X0,        L5_Y, "postgresql", "Landing Lake", "Bronze · full record", accent=BRONZE_LOCAL, w=NODE_W))
# Soft divider (same PII trust boundary · dev = same instance schema split)
soft_bx = L5_X0 + NODE_W + 8
parts.append(
    f'<line x1="{soft_bx}" y1="{L5_Y + 8}" x2="{soft_bx}" y2="{L5_Y + 102}"'
    f' stroke="{BRONZE_LOCAL}" stroke-width="1.4" stroke-dasharray="3 4" opacity="0.55"/>'
    f'<text x="{soft_bx}" y="{L5_Y + 55}" font-family="Helvetica" font-size="7"'
    f' fill="#94A3B8" text-anchor="middle" opacity="0.85">same PII zone</text>'
)
# 🔴 Raw PII Lake
parts.append(tool_node(L5_X0 + NODE_W + 22, L5_Y, "postgresql", "🔒 Raw PII Lake", "PII fields only", accent=EDGE_PII_LOCAL, w=NODE_W))
# PII Boundary thick red dashed line
pii_bx = L5_X0 + 2 * (NODE_W + 22) + 14
pii_by_top = L5_Y - 6
pii_by_bot = L5_Y + 112
parts.append(
    f'<line x1="{pii_bx}" y1="{pii_by_top}" x2="{pii_bx}" y2="{pii_by_bot}"'
    f' stroke="{EDGE_PII_LOCAL}" stroke-width="3" stroke-dasharray="6 4"/>'
    f'<rect x="{pii_bx - 18}" y="{L5_Y + 36}" width="36" height="38"'
    f' fill="{BG}" stroke="{EDGE_PII_LOCAL}" stroke-width="2" rx="6"/>'
    f'<rect x="{pii_bx - 6}" y="{L5_Y + 50}" width="12" height="10"'
    f' fill="#FFFFFF" rx="1.5"/>'
    f'<path d="M {pii_bx - 3.5} {L5_Y + 51} L {pii_bx - 3.5} {L5_Y + 46} '
    f'A 3.5 3.5 0 0 1 {pii_bx + 3.5} {L5_Y + 46} L {pii_bx + 3.5} {L5_Y + 51}" '
    f'stroke="#FFFFFF" stroke-width="1.6" fill="none"/>'
    f'<text x="{pii_bx}" y="{L5_Y + 69}" font-family="Helvetica" font-size="9"'
    f' font-weight="800" fill="{EDGE_PII_LOCAL}" text-anchor="middle">PII</text>'
)
# 🟢 Processed Lake (with pgvector for AI retrieval)
parts.append(tool_node(L5_X0 + 2 * (NODE_W + 22) + 32, L5_Y, "postgresql", "✓ Processed Lake", "dbt 5 layers + pgvector", accent=LAYER_COLORS[5], w=NODE_W))
parts.append(tool_node(L5_X0 + 3 * (NODE_W + 22) + 32, L5_Y, "redis",      "Redis",           "Cache + broker", accent=LAYER_COLORS[5], w=NODE_W))
parts.append(tool_node(L5_X0 + 4 * (NODE_W + 22) + 32, L5_Y, "minio",      "MinIO",           "S3 object storage", accent=LAYER_COLORS[5], w=NODE_W))

# tool quality tags
parts.append(tool_tag(L5_X0 + 18,                          L5_Y + 116, "dev: PG schema",  BRONZE_LOCAL))
parts.append(tool_tag(L5_X0 + (NODE_W + 22) + 18,          L5_Y + 116, "Fernet encrypted", EDGE_PII_LOCAL))
parts.append(tool_tag(L5_X0 + 2 * (NODE_W + 22) + 50,      L5_Y + 116, "RLS per Client",  LAYER_COLORS[5]))
parts.append(tool_tag(L5_X0 + 3 * (NODE_W + 22) + 50,      L5_Y + 116, "docker",          "#F59E0B"))
parts.append(tool_tag(L5_X0 + 4 * (NODE_W + 22) + 50,      L5_Y + 116, "self-hosted",     "#F59E0B"))

# TENANT ISOLATION callout (right)
ti_x = L5_X0 + 5 * (NODE_W + 22) + 50
ti_y = L5_Y - 2
ti_w = 200
ti_h = 116
parts.append(
    f'<rect x="{ti_x}" y="{ti_y}" width="{ti_w}" height="{ti_h}" fill="{NODE_BG}"'
    f' stroke="{LAYER_COLORS[5]}" stroke-width="2" rx="10"/>'
    f'<rect x="{ti_x}" y="{ti_y}" width="{ti_w}" height="4" fill="{LAYER_COLORS[5]}" rx="2"/>'
    f'<text x="{ti_x + ti_w//2}" y="{ti_y + 22}" font-family="Helvetica" font-size="11"'
    f' font-weight="800" fill="{LAYER_COLORS[5]}" text-anchor="middle"'
    f' letter-spacing="1.5">🛡 TENANT ISOLATION</text>'
)
parts.append(
    f'<rect x="{ti_x + 10}" y="{ti_y + 32}" width="{ti_w - 20}" height="34"'
    f' fill="{EDGE_PII_LOCAL}" fill-opacity="0.14" stroke="{EDGE_PII_LOCAL}"'
    f' stroke-opacity="0.55" stroke-width="1" rx="6"/>'
    f'<text x="{ti_x + 18}" y="{ti_y + 47}" font-family="Helvetica" font-size="10"'
    f' font-weight="800" fill="{EDGE_PII_LOCAL}">🏢 Agency</text>'
    f'<text x="{ti_x + 18}" y="{ti_y + 60}" font-family="Helvetica" font-size="9"'
    f' fill="{LABEL}">Physical · per-Agency DB + KMS</text>'
)
parts.append(
    f'<rect x="{ti_x + 10}" y="{ti_y + 72}" width="{ti_w - 20}" height="34"'
    f' fill="{LAYER_COLORS[5]}" fill-opacity="0.14" stroke="{LAYER_COLORS[5]}"'
    f' stroke-opacity="0.55" stroke-width="1" rx="6"/>'
    f'<text x="{ti_x + 18}" y="{ti_y + 87}" font-family="Helvetica" font-size="10"'
    f' font-weight="800" fill="{LAYER_COLORS[5]}">👤 Client</text>'
    f'<text x="{ti_x + 18}" y="{ti_y + 100}" font-family="Helvetica" font-size="9"'
    f' fill="{LABEL}">Logical · client_id RLS (in-Agency)</text>'
)

# ═══════════════════════════════════════════════════════════
# LAYER 6 — External Services
# ═══════════════════════════════════════════════════════════
parts.append(band_bg(6))
parts.append(layer_label(6, "External Services", "LLM + Observability", "Third-Party APIs"))

L6_Y = band_y(6) + 8
L6_X0 = PAD + LAYER_LABEL_W + 60

parts.append(section_title(L6_X0, L6_Y, "LLM STACK", EDGE_AI))
parts.append(tool_node(L6_X0, L6_Y + 14, "openrouter", "OpenRouter", "Default gateway · multi-vendor", accent=EDGE_AI, h=48, w=140))
parts.append(tool_node(L6_X0, L6_Y + 70, "bedrock",    "AWS Bedrock", "HIPAA · BAA · Claude managed", accent=EDGE_AI, h=48, w=140))
llm_models = [("anthropic", "Claude\nOpus"), ("anthropic", "Claude\nSonnet"), ("google", "Gemini\nFlash")]
for i, (slug, name) in enumerate(llm_models):
    parts.append(small_chip(L6_X0 + 150 + i * 85, L6_Y + 30, slug, name, accent=EDGE_AI, w=80, h=70))

OBS_X = L6_X0 + 430
parts.append(section_title(OBS_X, L6_Y, "OBSERVABILITY", "#14B8A6"))
parts.append(tool_node(OBS_X,         L6_Y + 10, "langfuse", "Langfuse",  "LLM call tracing",  accent="#14B8A6", h=100, w=140))
parts.append(tool_node(OBS_X + 150,   L6_Y + 10, "sentry",   "Sentry",    "Error monitoring",  accent="#14B8A6", h=100, w=140))

# Data Sources (categorical summary, no duplicate of L4 EXTRACT ADAPTERS)
DS_X = L6_X0 + 750
parts.append(section_title(DS_X, L6_Y, "DATA SOURCES (CATEGORIES)", LAYER_COLORS[6]))
ds_items = [
    ("googleads", "Ads"),
    ("hubspot",   "CRM"),
    ("attribution", "Attribution"),
    ("plus_more", "+more"),
]
for i, (slug, name) in enumerate(ds_items):
    chip_x = DS_X + i * 80
    chip_y = L6_Y + 14
    parts.append(small_chip(chip_x, chip_y, slug, name, accent=LAYER_COLORS[6], w=76, h=70))
parts.append(
    f'<text x="{DS_X}" y="{L6_Y + 100}" font-family="Helvetica" font-size="9"'
    f' fill="{DIM_LABEL}">Ads: GA4 · Meta · DV360 · StackAd. · TikTok</text>'
)
parts.append(
    f'<text x="{DS_X}" y="{L6_Y + 114}" font-family="Helvetica" font-size="9"'
    f' fill="{DIM_LABEL}">CRM: HubSpot   |   Attribution: LeadRX · LiveRamp · Quorum</text>'
)
parts.append(
    f'<text x="{DS_X}" y="{L6_Y + 128}" font-family="Helvetica" font-size="9"'
    f' fill="{DIM_LABEL}" font-style="italic">9 platforms detailed at L4 EXTRACT ADAPTERS</text>'
)

# ═══════════════════════════════════════════════════════════
# LAYER 7 — Infrastructure / Deployment
# ═══════════════════════════════════════════════════════════
parts.append(band_bg(7))
parts.append(layer_label(7, "Infrastructure", "Coolify PaaS", "Deployment Plane"))

L7_Y = band_y(7) + 18
L7_X0 = PAD + LAYER_LABEL_W + 60

COOL_X = L7_X0
parts.append(
    f'<rect x="{COOL_X}" y="{L7_Y}" width="280" height="120" fill="{NODE_BG}"'
    f' stroke="{LAYER_COLORS[7]}" stroke-width="3" rx="14"/>'
)
parts.append(
    f'<rect x="{COOL_X}" y="{L7_Y}" width="280" height="6" fill="{LAYER_COLORS[7]}" rx="3"/>'
)
icon = img_b64("coolify")
if icon:
    parts.append(f'<image href="{icon}" x="{COOL_X + 16}" y="{L7_Y + 24}" width="80" height="80"/>')
else:
    parts.append(
        f'<g transform="translate({COOL_X + 16},{L7_Y + 24}) scale(3.33)">'
        f'<path d="M12 0L2.196 5.625v12.75L12 24l9.804-5.625V5.625L12 0zm0 2.598l7.598 4.356v9.692L12 21.002 4.402 16.646V6.954L12 2.598z" fill="{LAYER_COLORS[7]}"/>'
        f'</g>'
    )
parts.append(
    f'<text x="{COOL_X + 116}" y="{L7_Y + 38}" font-family="Helvetica" font-size="22"'
    f' font-weight="800" fill="{LAYER_COLORS[7]}">Coolify</text>'
)
parts.append(
    f'<text x="{COOL_X + 116}" y="{L7_Y + 58}" font-family="Helvetica" font-size="11"'
    f' fill="{LABEL}" font-weight="600">PaaS Control Plane</text>'
)
for i, line in enumerate([
    "Docker orchestration",
    "GitOps CI/CD",
    "Env vars + DB backup",
    "Monitoring + Logs",
]):
    parts.append(
        f'<text x="{COOL_X + 116}" y="{L7_Y + 74 + i*12}" font-family="Helvetica"'
        f' font-size="10" fill="{DIM_LABEL}">&#10003; {line}</text>'
    )

parts.append(tool_node(L7_X0 + 320, L7_Y, "docker", "Docker", "Container runtime", accent=LAYER_COLORS[7], h=120))
parts.append(tool_node(L7_X0 + 500, L7_Y, "github", "GitHub", "Source + webhooks", accent=LAYER_COLORS[7], h=120))

CTRL_X = L7_X0 + 700
parts.append(section_title(CTRL_X, L7_Y + 4, "COOLIFY-MANAGED CONTAINERS", LAYER_COLORS[7]))
ctrl_items = [
    "backend (FastAPI)", "celery (worker)", "frontend (React)",
    "redis", "minio", "langfuse",
    "airflow-init", "airflow-web", "airflow-sched",
]
for i, name in enumerate(ctrl_items):
    bx = CTRL_X + (i % 3) * 130
    by = L7_Y + 14 + (i // 3) * 32
    parts.append(
        f'<rect x="{bx}" y="{by}" width="125" height="26" fill="{NODE_BG}"'
        f' stroke="{LAYER_COLORS[7]}" stroke-width="0.8" rx="5"/>'
    )
    parts.append(
        f'<circle cx="{bx + 10}" cy="{by + 13}" r="3" fill="{LAYER_COLORS[7]}"/>'
    )
    parts.append(
        f'<text x="{bx + 20}" y="{by + 17}" font-family="Helvetica" font-size="10"'
        f' font-weight="600" fill="{LABEL}">{name}</text>'
    )


# ═══════════════════════════════════════════════════════════
# Cross-layer data flow arrows — routed via margin highways
# ═══════════════════════════════════════════════════════════
# Two clear vertical channels: LEFT (between layer label and tools) and RIGHT (after tools)
LEFT_HW_X  = PAD + LAYER_LABEL_W + 32     # 252  — in 28px gap between label box (ends 220) and tools (start 280)
RIGHT_HW_X = CR - 340                # 1620 — clear of L1 USER TYPES (start 1680) and all other tools

def label_box(x: int, y: int, text: str, color: str, w: int = 100) -> str:
    """Pill-shaped label on top of an arrow path."""
    return (
        f'<rect x="{x - w//2}" y="{y - 10}" width="{w}" height="18" fill="{BG}"'
        f' stroke="{color}" stroke-width="1" rx="9"/>'
        f'<text x="{x}" y="{y + 3}" font-family="Helvetica" font-size="10"'
        f' font-weight="700" fill="{color}" text-anchor="middle">{text}</text>'
    )

# ─── Arrow 1: User traffic L1 → L2 (short, in band gap) ────────────
FLOW_X = PAD + LAYER_LABEL_W + 60 + 80
parts.append(arrow_down(FLOW_X, band_y(1) + BAND_HEIGHTS[1], band_y(2) + 18,
                       EDGE_USER, "HTTP/WS", width=2.5))
parts.append(arrow_down(FLOW_X, band_y(2) + BAND_HEIGHTS[2], band_y(3) + 12,
                       EDGE_USER, "auth+rls", width=2.5))

# ─── Arrow 2: ORM writes (L3 business services → L5 PostgreSQL) ────
# Route via RIGHT highway to avoid crossing L4 dbt and Compliance
orm_start_x = PAD + LAYER_LABEL_W + 60 + 1170  # right edge of business services row
orm_end_x   = PAD + LAYER_LABEL_W + 60 + 0 + 80  # PostgreSQL center (L5_X0+80)
y3_bot = band_y(3) + BAND_HEIGHTS[3] - 6        # exit L3 bottom
y_l4_l5_gap = band_y(5) - 4                     # in L4-L5 gap (y=858)
y5_top_hdr = band_y(5) + 12                     # in L5 header above PG_top
parts.append(
    f'<path d="M {orm_start_x} {y3_bot} '
    f'L {RIGHT_HW_X} {y3_bot} '
    f'L {RIGHT_HW_X} {y_l4_l5_gap} '
    f'L {orm_end_x} {y_l4_l5_gap} '
    f'L {orm_end_x} {band_y(5) + 25 - 4}" '
    f'stroke="{LAYER_COLORS[5]}" stroke-width="2.2" fill="none" stroke-dasharray="6 3"'
    f' marker-end="url(#arrow-{LAYER_COLORS[5][1:]})"/>'
)
parts.append(label_box(RIGHT_HW_X, (y3_bot + y_l4_l5_gap)//2, "ORM writes", LAYER_COLORS[5], 90))

# ─── Arrow 3: (1) EXTRACT — L6 sources → L4 adapters (enters via L3-L4 gap)
# Layer offsets (from defined constants):
#   L4_Y = band_y(4) + 12 = 646
#   L6_Y = band_y(6) + 8 = 1048
#   DS_X = 1030, source chips w=76, spacing 80 → row 0 ends at x=1426
#   ETL_X = 640, adapter chips w=82, spacing 86 → row 0 ends at x=1066
src_x_right = 1436                                     # right of last source chip (1426 + 10)
src_y = 1097                                            # source row 0 mid (L6_Y + 14 + 35)
y_l3_l4_gap = 630                                       # in 8px L3-L4 gap (626-634)
adapter_top_x = 853                                     # HubSpot row 0 center (812 + 41)
adapter_top_y = 658                                     # 2px above adapter row 0 top (660)
parts.append(
    f'<path d="M {src_x_right} {src_y} '
    f'L {RIGHT_HW_X} {src_y} '
    f'L {RIGHT_HW_X} {y_l3_l4_gap} '
    f'L {adapter_top_x} {y_l3_l4_gap} '
    f'L {adapter_top_x} {adapter_top_y}" '
    f'stroke="{EDGE_DATA}" stroke-width="2.8" fill="none"'
    f' marker-end="url(#arrow-{EDGE_DATA[1:]})"/>'
)
parts.append(label_box(RIGHT_HW_X, (src_y + y_l3_l4_gap)//2, "(1) EXTRACT", EDGE_DATA, 100))

# ─── Arrow 4: (2) LOAD raw_* — exit right of adapter group → past dbt right → L5 header
# adapter row 0 ends at y=722, row 1 ends at y=788 (with h=62, v-spacing=66)
# dbt section: title baseline y=796 (text ≈786-798), boxes y=806-861
# Safe horizontal channel: y=802 (below text, above boxes)
adapter_exit_x = 1070                                   # in 9px gap (chip 4 end 1066 ← → compliance 1075)
adapter_exit_y = 789                                    # 1px below row 1 bottom (788)
y_horiz_below_dbt_title = 802                           # between dbt title text (798) and boxes (806)
dbt_right_x = 1450                                      # past Field Mapping (ends 1140) + buffer
y_l5_header = 876                                       # in L5 header above PG/DuckDB top (887)
warehouse_x = 540                                       # DuckDB column center
warehouse_top = 883                                     # 4px above DuckDB top
parts.append(
    f'<path d="M {adapter_exit_x} {adapter_exit_y} '
    f'L {adapter_exit_x} {y_horiz_below_dbt_title} '
    f'L {dbt_right_x} {y_horiz_below_dbt_title} '
    f'L {dbt_right_x} {y_l5_header} '
    f'L {warehouse_x} {y_l5_header} '
    f'L {warehouse_x} {warehouse_top}" '
    f'stroke="{EDGE_DATA}" stroke-width="2.5" fill="none"'
    f' marker-end="url(#arrow-{EDGE_DATA[1:]})"/>'
)
parts.append(label_box(dbt_right_x, (y_horiz_below_dbt_title + y_l5_header)//2, "(2) LOAD raw_*", EDGE_DATA, 110))

# ─── Arrow 5: httpx → LLM (L3 agents → L6 OpenRouter) via LEFT highway
agent_exit_x   = PAD + LAYER_LABEL_W + 60 + 200          # Persona chip left edge area
agent_exit_y   = band_y(3) + 12 - 4                       # exit chip TOP into L2-L3 gap
y_l2_l3_gap    = band_y(3) - 4                            # in 8px gap
openrouter_x   = PAD + LAYER_LABEL_W + 60 + 60            # OpenRouter left edge
openrouter_y   = band_y(6) + 10 + 50                      # OpenRouter mid
parts.append(
    f'<path d="M {agent_exit_x} {agent_exit_y} '
    f'L {agent_exit_x} {y_l2_l3_gap} '       # up into L2-L3 gap
    f'L {LEFT_HW_X} {y_l2_l3_gap} '          # left to LEFT highway
    f'L {LEFT_HW_X} {openrouter_y} '         # down through L3,L4,L5 to L6
    f'L {openrouter_x} {openrouter_y}" '     # right into OpenRouter
    f'stroke="{EDGE_AI}" stroke-width="2.5" fill="none"'
    f' marker-end="url(#arrow-{EDGE_AI[1:]})"/>'
)
parts.append(label_box(LEFT_HW_X, y_l2_l3_gap - 14, "httpx→LLM", EDGE_AI, 70))

# ═══════════════════════════════════════════════════════════
# Compliance right sidebar + explicit per-layer connectors (cross-cutting, mandatory)
# ═══════════════════════════════════════════════════════════
COMP_X = CR + 40
COMP_W = W - COMP_X - 30
SPINE_X = COMP_X - 16        # Card left side; keep connector lines outside the card frame

# 1) Explicit connectors: each band -> spine (proves "touches every feature")
for layer in range(1, 8):
    ay = band_y(layer) + BAND_HEIGHTS[layer] // 2
    parts.append(
        f'<line x1="{CR - 8}" y1="{ay}" x2="{SPINE_X}" y2="{ay}"'
        f' stroke="{EDGE_GUARD}" stroke-width="1.4" stroke-dasharray="4 4" opacity="0.55"/>'
        f'<circle cx="{SPINE_X}" cy="{ay}" r="3.5" fill="{EDGE_GUARD}" opacity="0.85"/>'
    )

# 2) Central vertical spine (joins all anchors)
SPINE_TOP = band_y(1) + BAND_HEIGHTS[1] // 2 - 8
SPINE_BOT = band_y(7) + BAND_HEIGHTS[7] // 2 + 8
parts.append(
    f'<line x1="{SPINE_X}" y1="{SPINE_TOP}" x2="{SPINE_X}" y2="{SPINE_BOT}"'
    f' stroke="{EDGE_GUARD}" stroke-width="2" opacity="0.7"/>'
)

# 3) Top card: title + 3 regulations
TOP_Y = band_y(2) - 14
TOP_H = 220
parts.append(
    f'<defs><linearGradient id="grad-comp-top" x1="0%" y1="0%" x2="0%" y2="100%">'
    f'<stop offset="0%" stop-color="{EDGE_GUARD}" stop-opacity="0.20"/>'
    f'<stop offset="100%" stop-color="{EDGE_GUARD}" stop-opacity="0.05"/>'
    f'</linearGradient></defs>'
    f'<rect x="{COMP_X}" y="{TOP_Y}" width="{COMP_W}" height="{TOP_H}"'
    f' fill="url(#grad-comp-top)" stroke="{EDGE_GUARD}" stroke-width="2.5" rx="14"/>'
    f'<rect x="{COMP_X}" y="{TOP_Y}" width="{COMP_W}" height="6" fill="{EDGE_GUARD}" rx="3"/>'
)
icon = img_b64("compliance")
if icon:
    parts.append(
        f'<image href="{icon}" x="{COMP_X + COMP_W // 2 - 22}" y="{TOP_Y + 18}"'
        f' width="44" height="44"/>'
    )
parts.append(
    f'<text x="{COMP_X + COMP_W // 2}" y="{TOP_Y + 80}" font-family="Helvetica"'
    f' font-size="18" font-weight="800" fill="{EDGE_GUARD}" text-anchor="middle">'
    f'COMPLIANCE</text>'
    f'<text x="{COMP_X + COMP_W // 2}" y="{TOP_Y + 98}" font-family="Helvetica"'
    f' font-size="10" font-weight="600" fill="{LABEL}" text-anchor="middle">'
    f'Mandatory · Cross-cutting</text>'
    f'<text x="{COMP_X + COMP_W // 2}" y="{TOP_Y + 113}" font-family="Helvetica"'
    f' font-size="9" font-style="italic" fill="{DIM_LABEL}" text-anchor="middle">'
    f'Required by all L1 → L7</text>'
)
regs = [
    ("GDPR",  "EU · 30d"),
    ("CCPA",  "CA · 45d"),
    ("HIPAA", "Health · 60d"),
]
for i, (code, hint) in enumerate(regs):
    by = TOP_Y + 128 + i * 30
    parts.append(
        f'<rect x="{COMP_X + 14}" y="{by}" width="{COMP_W - 28}" height="26"'
        f' fill="{EDGE_GUARD}" fill-opacity="0.14" stroke="{EDGE_GUARD}"'
        f' stroke-opacity="0.6" stroke-width="1" rx="7"/>'
        f'<text x="{COMP_X + 24}" y="{by + 17}" font-family="Helvetica"'
        f' font-size="12" font-weight="800" fill="{EDGE_GUARD}">{code}</text>'
        f'<text x="{COMP_X + COMP_W - 24}" y="{by + 17}" font-family="Helvetica"'
        f' font-size="10" fill="{LABEL}" text-anchor="end">{hint}</text>'
    )

# 4) Bottom card: capabilities
BOT_Y = band_y(5) + 10
BOT_H = 240
parts.append(
    f'<defs><linearGradient id="grad-comp-bot" x1="0%" y1="0%" x2="0%" y2="100%">'
    f'<stop offset="0%" stop-color="{EDGE_GUARD}" stop-opacity="0.18"/>'
    f'<stop offset="100%" stop-color="{EDGE_GUARD}" stop-opacity="0.04"/>'
    f'</linearGradient></defs>'
    f'<rect x="{COMP_X}" y="{BOT_Y}" width="{COMP_W}" height="{BOT_H}"'
    f' fill="url(#grad-comp-bot)" stroke="{EDGE_GUARD}" stroke-width="2.5" rx="14"/>'
    f'<rect x="{COMP_X}" y="{BOT_Y}" width="{COMP_W}" height="6" fill="{EDGE_GUARD}" rx="3"/>'
)
parts.append(
    f'<text x="{COMP_X + COMP_W // 2}" y="{BOT_Y + 26}" font-family="Helvetica"'
    f' font-size="11" font-weight="800" fill="{EDGE_GUARD}" text-anchor="middle"'
    f' letter-spacing="2">▸ CAPABILITIES</text>'
)
caps = [
    "PHI Detector",
    "Anonymizer · SHA-256",
    "Agency Salt isolation",
    "IP truncate (v4/24 · v6/48)",
    "Fernet field enc.",
    "Audit Log · 6y",
    "DSAR (30 / 45 / 30 d)",
    "Retention engine",
    "Breach 72h · BAA",
    "Key rotation",
    "Data minimization",
]
cy = BOT_Y + 50
for cap in caps:
    parts.append(
        f'<circle cx="{COMP_X + 18}" cy="{cy - 4}" r="2.5" fill="{EDGE_GUARD}"/>'
        f'<text x="{COMP_X + 26}" y="{cy}" font-family="Helvetica" font-size="10.5"'
        f' fill="{LABEL}">{cap}</text>'
    )
    cy += 17



# ═══════════════════════════════════════════════════════════
# Coolify management boundary
# ═══════════════════════════════════════════════════════════

ctrl_top = band_y(2) - 4
ctrl_bot = band_y(7) - 4
ctrl_x = PAD + LAYER_LABEL_W + 20 - 6
ctrl_w = CR - ctrl_x + 6
parts.append(
    f'<rect x="{ctrl_x}" y="{ctrl_top}" width="{ctrl_w}" height="{ctrl_bot - ctrl_top}"'
    f' fill="none" stroke="{LAYER_COLORS[7]}" stroke-width="2.5" stroke-dasharray="10 6" rx="16" opacity="0.55"/>'
)

# ═══════════════════════════════════════════════════════════
# Legend
# ═══════════════════════════════════════════════════════════
LEG_Y = H - 80
LEG_X = CR - 700
parts.append(
    f'<rect x="{LEG_X - 16}" y="{LEG_Y - 16}" width="700" height="68"'
    f' fill="{NODE_BG}" stroke="{STROKE}" stroke-width="1" rx="10"/>'
)
parts.append(
    f'<text x="{LEG_X}" y="{LEG_Y + 4}" font-family="Helvetica" font-size="12"'
    f' font-weight="800" fill="{TITLE}" letter-spacing="1.5">DATA FLOW LEGEND</text>'
)

legend_items = [
    (EDGE_USER,   "User Traffic"),
    (EDGE_AI,     "LLM Calls"),
    (EDGE_DATA,   "ETL/ELT Data"),
    (EDGE_GUARD,  "Compliance"),
    (EDGE_DEPLOY, "Deploy/Manage"),
]
for i, (color, name) in enumerate(legend_items):
    lx = LEG_X + i * 140
    ly = LEG_Y + 30
    parts.append(
        f'<line x1="{lx}" y1="{ly}" x2="{lx + 30}" y2="{ly}"'
        f' stroke="{color}" stroke-width="3" marker-end="url(#arrow-{color[1:]})"/>'
    )
    parts.append(
        f'<text x="{lx + 38}" y="{ly + 4}" font-family="Helvetica" font-size="11"'
        f' font-weight="600" fill="{LABEL}">{name}</text>'
    )

parts.append(
    f'<text x="{(CR+PAD)//2}" y="{H - 16}" font-family="Helvetica" font-size="10"'
    f' fill="{DIM_LABEL}" text-anchor="middle">'
    f'ReceptivIQ Platform &#183; Layered Stack v1.0 (EN)  &#183;  Generated by dev-stack-layered-en.py</text>'
)

parts.append('</svg>')
svg_content = "\n".join(parts)
OUT_SVG.write_text(svg_content)
print(f"OK wrote {OUT_SVG} ({len(svg_content):,} bytes)")

# Convert SVG -> PNG
converters = [
    ["rsvg-convert", str(OUT_SVG), "-o", str(OUT_PNG), "-w", str(W)],
    ["inkscape", str(OUT_SVG), f"--export-filename={OUT_PNG}", f"--export-width={W}"],
    ["convert", "-density", "150", str(OUT_SVG), str(OUT_PNG)],
]
converted = False
for cmd in converters:
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        if result.returncode == 0 and OUT_PNG.exists():
            print(f"OK wrote {OUT_PNG} via {cmd[0]}")
            converted = True
            break
    except (FileNotFoundError, subprocess.TimeoutExpired):
        continue

if not converted:
    print("! PNG conversion skipped (install rsvg-convert / inkscape / imagemagick to enable)")
