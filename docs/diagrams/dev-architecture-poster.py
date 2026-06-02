"""
ReceptivIQ — Tool-centric Technical Architecture (hand-crafted SVG)

Design intent (per user feedback):
- Show TOOLS used, not implementation details
- Data flow is the primary axis (arrows with labels)
- No table declarations, no router lists, no service module breakdowns
- One icon + one label per tool; arrows carry the "what flows" annotations

Output: dev-architecture-poster.{png,svg}
"""
from __future__ import annotations
import base64
import subprocess
from pathlib import Path

ICONS_DIR = Path("icons")
OUT_SVG = Path("dev-architecture-poster.svg")
OUT_PNG = Path("dev-architecture-poster.png")


def img_b64(name: str) -> str:
    p = ICONS_DIR / f"{name}.png"
    if not p.exists():
        return ""
    return f"data:image/png;base64,{base64.b64encode(p.read_bytes()).decode('ascii')}"


# ───────── Theme ─────────
BG          = "#0B1220"
NODE_BG     = "#13203a"
TITLE       = "#F8FAFC"
SUBTITLE    = "#94A3B8"
LABEL       = "#E2E8F0"
EDGE_LABEL  = "#94A3B8"
STROKE      = "#1E293B"

# Edge colors by data class
EDGE_INGEST = "#A855F7"   # purple — raw ingest
EDGE_DATA   = "#10B981"   # emerald — internal data
EDGE_USER   = "#06B6D4"   # cyan — user traffic
EDGE_AI     = "#EC4899"   # pink — LLM
EDGE_OBS    = "#14B8A6"   # teal — observability
EDGE_DEPLOY = "#F59E0B"   # amber — devops

W, H = 1900, 1180
PAD = 60


# ─────────  Helpers ─────────

def node(x: int, y: int, slug: str, label: str, sublabel: str = "",
         w: int = 150, h: int = 130, accent: str = "#475569") -> str:
    """A tool node: rounded card with icon + tool name + role label."""
    icon_size = 64
    out = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{NODE_BG}"'
        f' stroke="{accent}" stroke-width="1.5" rx="12" />',
        f'<image href="{img_b64(slug)}" x="{x + (w-icon_size)//2}" y="{y+14}"'
        f' width="{icon_size}" height="{icon_size}" />',
        f'<text x="{x + w//2}" y="{y + 96}" font-family="Helvetica" font-size="13"'
        f' font-weight="700" fill="{LABEL}" text-anchor="middle">{label}</text>',
    ]
    if sublabel:
        out.append(
            f'<text x="{x + w//2}" y="{y + 115}" font-family="Helvetica"'
            f' font-size="10" fill="{SUBTITLE}" text-anchor="middle">{sublabel}</text>'
        )
    return "\n".join(out)


def small_node(x: int, y: int, slug: str, label: str,
               w: int = 120, h: int = 90, accent: str = "#475569") -> str:
    icon_size = 44
    return "\n".join([
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{NODE_BG}"'
        f' stroke="{accent}" stroke-width="1.2" rx="10" />',
        f'<image href="{img_b64(slug)}" x="{x + (w-icon_size)//2}" y="{y+10}"'
        f' width="{icon_size}" height="{icon_size}" />',
        f'<text x="{x + w//2}" y="{y + 75}" font-family="Helvetica" font-size="11"'
        f' font-weight="600" fill="{LABEL}" text-anchor="middle">{label}</text>',
    ])


def grp_node(x: int, y: int, items: list[tuple[str, str]], title: str,
             w: int = 220, accent: str = "#475569") -> str:
    """A grouped node showing multiple logos (e.g., 15 data sources as a single conceptual block)."""
    h = 130
    out = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{NODE_BG}"'
        f' stroke="{accent}" stroke-width="1.5" rx="12" />',
        f'<text x="{x + w//2}" y="{y + 22}" font-family="Helvetica" font-size="12"'
        f' font-weight="700" fill="{accent}" text-anchor="middle">{title}</text>',
    ]
    # Display icons in a grid
    n = len(items)
    cols = min(n, 5)
    rows = (n + cols - 1) // cols
    icon = 28
    gx = (w - cols * icon - (cols-1) * 6) // 2
    gy = 32
    for i, (slug, _) in enumerate(items):
        col = i % cols
        row = i // cols
        ix = x + gx + col * (icon + 6)
        iy = y + gy + row * (icon + 4)
        out.append(
            f'<image href="{img_b64(slug)}" x="{ix}" y="{iy}"'
            f' width="{icon}" height="{icon}" />'
        )
    return "\n".join(out)


def edge(x1: int, y1: int, x2: int, y2: int, color: str = "#475569",
         label: str = "", label_x: int | None = None, label_y: int | None = None,
         dashed: bool = False, width: float = 2.2) -> str:
    """Straight arrow with optional mid-point label."""
    dash = ' stroke-dasharray="6 6"' if dashed else ''
    out = [
        f'<path d="M {x1} {y1} L {x2} {y2}" stroke="{color}" stroke-width="{width}"'
        f' fill="none"{dash} marker-end="url(#arrow)" />'
    ]
    if label:
        lx = label_x if label_x is not None else (x1 + x2) // 2
        ly = label_y if label_y is not None else (y1 + y2) // 2 - 6
        # background pill behind label
        out.append(
            f'<rect x="{lx-len(label)*3-6}" y="{ly-10}" width="{len(label)*6+12}"'
            f' height="16" fill="{BG}" rx="3" />'
        )
        out.append(
            f'<text x="{lx}" y="{ly+2}" font-family="Helvetica" font-size="10"'
            f' font-weight="600" fill="{color}" text-anchor="middle">{label}</text>'
        )
    return "\n".join(out)


def bent_edge(x1: int, y1: int, x2: int, y2: int, mid_x: int | None = None,
              color: str = "#475569", label: str = "",
              dashed: bool = False, width: float = 2.2) -> str:
    """L-shaped (bent) arrow: out from x1,y1 to mid_x then to x2,y2."""
    mid_x = mid_x if mid_x is not None else (x1 + x2) // 2
    dash = ' stroke-dasharray="6 6"' if dashed else ''
    out = [
        f'<path d="M {x1} {y1} L {mid_x} {y1} L {mid_x} {y2} L {x2} {y2}"'
        f' stroke="{color}" stroke-width="{width}" fill="none"{dash}'
        f' marker-end="url(#arrow)" />'
    ]
    if label:
        lx = (mid_x + x2) // 2
        ly = y2 - 8
        out.append(
            f'<rect x="{lx-len(label)*3-6}" y="{ly-10}" width="{len(label)*6+12}"'
            f' height="16" fill="{BG}" rx="3" />'
        )
        out.append(
            f'<text x="{lx}" y="{ly+2}" font-family="Helvetica" font-size="10"'
            f' font-weight="600" fill="{color}" text-anchor="middle">{label}</text>'
        )
    return "\n".join(out)


# ════════════════════════ Begin SVG ════════════════════════
parts: list[str] = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">',
    f'<rect width="{W}" height="{H}" fill="{BG}" />',
    '<defs>'
    '  <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"'
    '     markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
    f'    <path d="M 0 0 L 10 5 L 0 10 z" fill="#94A3B8"/></marker>'
    '</defs>',

    # Title
    f'<text x="{W//2}" y="50" font-family="Helvetica" font-size="32"'
    f' font-weight="700" fill="{TITLE}" text-anchor="middle">'
    f'ReceptivIQ Platform &#8212; Technical Architecture</text>',
    f'<text x="{W//2}" y="76" font-family="Helvetica" font-size="14"'
    f' fill="{SUBTITLE}" text-anchor="middle">'
    f'tool-centric data flow  &#183;  arrows show what data moves where</text>',
]

# ═════════════ DevOps strip (top-right corner) ═════════════
DEV_Y = 110
DEV_X = W - PAD - 460
parts.append(
    f'<text x="{DEV_X}" y="{DEV_Y-8}" font-family="Helvetica" font-size="12"'
    f' font-weight="700" fill="{EDGE_DEPLOY}">DEV &amp; DEPLOY</text>'
)
parts.append(small_node(DEV_X,        DEV_Y, "github",        "GitHub",         accent=EDGE_DEPLOY))
parts.append(small_node(DEV_X+150,    DEV_Y, "docker",        "Docker Compose", accent=EDGE_DEPLOY))
parts.append(small_node(DEV_X+300,    DEV_Y, "render",        "Render",         accent=EDGE_DEPLOY))
parts.append(edge(DEV_X+120, DEV_Y+45, DEV_X+150, DEV_Y+45, EDGE_DEPLOY, "push",   width=1.6))
parts.append(edge(DEV_X+270, DEV_Y+45, DEV_X+300, DEV_Y+45, EDGE_DEPLOY, "deploy", width=1.6))

# ═════════════ Users (top-left corner) ═════════════
USR_X, USR_Y = PAD, 110
parts.append(
    f'<text x="{USR_X}" y="{USR_Y-8}" font-family="Helvetica" font-size="12"'
    f' font-weight="700" fill="{EDGE_USER}">END USERS</text>'
)
# We don't have a user icon, use a stylized circle + label
parts.append(small_node(USR_X,         USR_Y, "staff",   "Agency Staff",  accent=EDGE_USER))
parts.append(small_node(USR_X+150,     USR_Y, "client",  "Brand Clients", accent=EDGE_USER))

# ═════════════ Data sources (left side) ═════════════
SRC_X, SRC_Y = PAD, 290
DATA_SOURCES = [
    ("ga4", "GA4"), ("meta", "Meta"), ("hubspot", "HubSpot"),
    ("tiktok", "TikTok"), ("dv360", "DV360"),
    ("stackadapt", "StackAdapt"), ("trade_desk", "TTD"),
    ("salesforce", "Salesforce"), ("liveramp", "LiveRamp"), ("placeriq", "PlacerIQ"),
    ("experian", "Experian"), ("netsuite", "NetSuite"),
    ("googleads", "GoogleAds"), ("leadrx", "LeadRX"), ("quorum", "Quorum"),
]
parts.append(grp_node(SRC_X, SRC_Y, DATA_SOURCES, "15 EXTERNAL APIs", w=270, accent=EDGE_INGEST))

# ═════════════ Pipeline row: Airflow → Snowflake → dbt ═════════════
PIPE_Y = 290
AIR_X = SRC_X + 320
SNOW_X = AIR_X + 220
DBT_X = SNOW_X + 220
parts.append(node(AIR_X,  PIPE_Y, "apacheairflow", "Airflow",   "DAG scheduler",         accent=EDGE_INGEST))
parts.append(node(SNOW_X, PIPE_Y, "snowflake",     "Snowflake", "warehouse (DuckDB dev)", accent=EDGE_INGEST))
parts.append(node(DBT_X,  PIPE_Y, "dbt",           "dbt",       "in-warehouse transform", accent=EDGE_INGEST))

# Data source → Airflow
parts.append(edge(SRC_X+270, SRC_Y+65, AIR_X-2, PIPE_Y+65,
                  EDGE_INGEST, "OAuth / API Key pulls"))
# Airflow → Snowflake
parts.append(edge(AIR_X+150, PIPE_Y+65, SNOW_X-2, PIPE_Y+65,
                  EDGE_INGEST, "Load raw"))
# Snowflake → dbt
parts.append(edge(SNOW_X+150, PIPE_Y+65, DBT_X-2, PIPE_Y+65,
                  EDGE_INGEST, "ELT transform"))

# ═════════════ Application core: FastAPI ═════════════
API_X, API_Y = SNOW_X - 80, 520
parts.append(node(API_X, API_Y, "fastapi", "FastAPI", "Python 3.9 · async", w=220, h=140,
                  accent=EDGE_DATA))

# dbt → FastAPI (marts feed back to app)
parts.append(bent_edge(DBT_X+75, PIPE_Y+130, API_X+200, API_Y,
                       mid_x=DBT_X+75, color=EDGE_DATA, label="marts → analytical reads"))

# ═════════════ Frontend ═════════════
WEB_X, WEB_Y = PAD, API_Y + 10
parts.append(node(WEB_X, WEB_Y, "react", "React 19",
                  "Vite · TypeScript · Ant Design", w=240, h=140, accent=EDGE_USER))

# Users (top-left badges) → React below
parts.append(bent_edge(USR_X+60, USR_Y+90, WEB_X+80, WEB_Y-2,
                       mid_x=WEB_X+80, color=EDGE_USER, label="login"))
parts.append(bent_edge(USR_X+210, USR_Y+90, WEB_X+160, WEB_Y-2,
                       mid_x=WEB_X+160, color=EDGE_USER, label="portal"))

# React → FastAPI
parts.append(edge(WEB_X+240, WEB_Y+70, API_X-2, API_Y+70, EDGE_USER, "HTTPS / WSS"))

# ═════════════ Below FastAPI: Postgres, Redis, Celery ═════════════
DATA_ROW_Y = 720
PG_X     = WEB_X
REDIS_X  = PG_X + 200
CELERY_X = REDIS_X + 200
S3_X     = CELERY_X + 200
parts.append(node(PG_X,     DATA_ROW_Y, "neon",       "PostgreSQL",   "+pgvector · Neon prod", w=180, accent=EDGE_DATA))
parts.append(node(REDIS_X,  DATA_ROW_Y, "redis",      "Redis 7",      "cache · broker · sessions", w=180, accent=EDGE_DATA))
parts.append(node(CELERY_X, DATA_ROW_Y, "celery",     "Celery",       "async workers", w=180, accent=EDGE_DATA))
parts.append(node(S3_X,     DATA_ROW_Y, "minio",      "MinIO / S3",   "object storage", w=180, accent=EDGE_DATA))

# FastAPI → Postgres / Redis / Celery
parts.append(edge(API_X+30,  API_Y+140, PG_X+90,    DATA_ROW_Y-2, EDGE_DATA, "CRUD",       width=2.0))
parts.append(edge(API_X+90,  API_Y+140, REDIS_X+90, DATA_ROW_Y-2, EDGE_DATA, "cache/sess", width=2.0))
parts.append(edge(API_X+150, API_Y+140, CELERY_X+90, DATA_ROW_Y-2, EDGE_DATA, "tasks",     width=2.0))
parts.append(edge(API_X+190, API_Y+140, S3_X+90,    DATA_ROW_Y-2, EDGE_DATA, "files",     width=2.0))

# Airflow uses Celery? No — Airflow is separate. Celery → SMTP (emails)
# show that flow at the bottom

# ═════════════ LLM channel (right side of FastAPI) ═════════════
OR_X, OR_Y = DBT_X + 30, API_Y
CLAUDE_X = OR_X + 180
parts.append(node(OR_X,    OR_Y, "openrouter", "OpenRouter", "LLM gateway", w=160, h=140, accent=EDGE_AI))
parts.append(node(CLAUDE_X, OR_Y, "anthropic", "Claude",     "Opus 4.7 (Anthropic)", w=180, h=140, accent=EDGE_AI))

# FastAPI → OpenRouter → Claude
parts.append(edge(API_X+220, API_Y+70, OR_X-2, OR_Y+70, EDGE_AI, "chat completions"))
parts.append(edge(OR_X+160, OR_Y+70, CLAUDE_X-2, OR_Y+70, EDGE_AI, "Anthropic API"))

# ═════════════ Observability + Email (bottom right) ═════════════
OBS_Y = DATA_ROW_Y
SENTRY_X   = S3_X + 200
LANGFUSE_X = SENTRY_X + 175
SMTP_X     = LANGFUSE_X + 175
parts.append(small_node(SENTRY_X,   OBS_Y+10, "sentry",   "Sentry",   accent=EDGE_OBS, w=160, h=110))
parts.append(small_node(LANGFUSE_X, OBS_Y+10, "langfuse", "Langfuse", accent=EDGE_OBS, w=160, h=110))
parts.append(small_node(SMTP_X,     OBS_Y+10, "smtp",     "SMTP",     accent=EDGE_OBS, w=160, h=110))

# FastAPI → Sentry (errors)
parts.append(bent_edge(API_X+220, API_Y+115, SENTRY_X+80, OBS_Y+10,
                       mid_x=SENTRY_X+80, color=EDGE_OBS, label="errors", dashed=True))
# Claude → Langfuse (trace) — actually OpenRouter or Brain pushes traces
parts.append(bent_edge(OR_X+80, OR_Y+140, LANGFUSE_X+80, OBS_Y+10,
                       mid_x=LANGFUSE_X+80, color=EDGE_OBS, label="LLM traces", dashed=True))
# Celery → SMTP (report emails)
parts.append(edge(CELERY_X+180, DATA_ROW_Y+65, SMTP_X-2, OBS_Y+65,
                  EDGE_OBS, "report emails", dashed=True))

# ═════════════ Supporting tools strip (full width) ═════════════
TOOLS_Y = 970
parts.append(
    f'<text x="{PAD}" y="{TOOLS_Y}" font-family="Helvetica" font-size="13"'
    f' font-weight="700" fill="{SUBTITLE}">Supporting tools (cross-cutting):</text>'
)
support_tools = [
    ("postgresql",    "Alembic"),
    ("apacheairflow", "Airflow Web UI"),
    ("github",        "GitHub Actions"),
    ("snowflake",     "DuckDB (dev)"),
    ("fastapi",       "Pydantic v2"),
    ("anthropic",     "Fernet crypto"),
    ("redis",         "JWT + jti"),
    ("compliance",    "PHI Detector"),
    ("audience",      "Audit logs"),
]
cols = len(support_tools)
col_w = (W - 2*PAD - 60) // cols
for i, (slug, label) in enumerate(support_tools):
    parts.append(small_node(PAD + i*col_w, TOOLS_Y + 15, slug, label,
                            accent="#475569", w=col_w - 10, h=90))

# Footer
parts.append(
    f'<text x="{W//2}" y="{H-20}" font-family="Helvetica" font-size="11"'
    f' fill="{SUBTITLE}" text-anchor="middle">'
    f'Edge colors: '
    f'<tspan fill="{EDGE_INGEST}">&#9632; raw ingest</tspan> &#183; '
    f'<tspan fill="{EDGE_DATA}">&#9632; internal data</tspan> &#183; '
    f'<tspan fill="{EDGE_USER}">&#9632; user traffic</tspan> &#183; '
    f'<tspan fill="{EDGE_AI}">&#9632; LLM</tspan> &#183; '
    f'<tspan fill="{EDGE_OBS}">&#9632; observability</tspan> &#183; '
    f'<tspan fill="{EDGE_DEPLOY}">&#9632; deploy</tspan></text>'
)

parts.append('</svg>')


def main() -> None:
    OUT_SVG.write_text("\n".join(parts), encoding="utf-8")
    print(f"✓ wrote {OUT_SVG} ({OUT_SVG.stat().st_size // 1024} KB)")
    subprocess.run(
        ["rsvg-convert", "-w", str(W), "-h", str(H),
         str(OUT_SVG), "-o", str(OUT_PNG)],
        check=True,
    )
    print(f"✓ wrote {OUT_PNG} ({OUT_PNG.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
