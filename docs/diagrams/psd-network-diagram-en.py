#!/usr/bin/env python3
"""ReceptivIQ PSD · Network Diagram (English)

6-layer end-to-end data flow: External Sources → ELT 8-step pipeline → 3-Lake Warehouse → Core AI Brain
                → Pillar Agents → Application / Client Portal.
Cross-cutting: Compliance outer frame (GDPR/CCPA/HIPAA/SOC 2 + Data Residency), PII Segregation Boundary.

Output: docs/psd/network-diagram-en.{svg, png}
"""
from __future__ import annotations
import base64
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
ICONS = ROOT / "icons"
OUT_DIR = ROOT.parent / "psd"

# ── Theme ────────────────────────────────────────────────
BG          = "#0B1220"
NODE_BG     = "#111B2D"
NODE_BG_2   = "#0F1729"
TITLE       = "#F8FAFC"
LABEL       = "#E2E8F0"
DIM_LABEL   = "#94A3B8"

# Data flow colors
EDGE_USER   = "#A78BFA"   # User flow
EDGE_DATA   = "#22D3EE"   # Data
EDGE_AI     = "#F472B6"   # AI call
EDGE_GUARD  = "#F59E0B"   # Compliance
EDGE_PII    = "#EF4444"   # PII boundary (highlighted red)

# Per-layer accent
LAYER_COLORS = {
    1: "#0EA5E9",   # External Sources — sky
    2: "#10B981",   # ELT Pipeline — emerald
    3: "#8B5CF6",   # Two-Lake — violet
    4: "#EC4899",   # AI Brain — pink
    5: "#F97316",   # Pillar Agents — orange
    6: "#14B8A6",   # Application — teal
}

# Canvas
W, H = 2200, 1760
PAD = 40
LAYER_LABEL_W = 220

BAND_TOP = 170
BAND_GAP = 40  # widened to host inter-layer flow strips
BAND_HEIGHTS = {1: 220, 2: 240, 3: 230, 4: 220, 5: 200, 6: 180}

# ── Helpers ──────────────────────────────────────────────
def img_b64(name: str) -> str:
    p = ICONS / f"{name}.png"
    if not p.exists():
        return ""
    return f"data:image/png;base64,{base64.b64encode(p.read_bytes()).decode('ascii')}"


def band_y(layer: int) -> int:
    y = BAND_TOP
    for i in range(1, layer):
        y += BAND_HEIGHTS[i] + BAND_GAP
    return y


def text_w(s: str, fs: int = 11) -> int:
    cn = sum(1 for c in s if ord(c) > 127)
    en = len(s) - cn
    return int(cn * fs + en * fs * 0.6)


# ── Left-side layer labels ───────────────────────────────
def layer_label(layer: int, cn: str, en: str, desc: str) -> str:
    y0 = band_y(layer)
    h = BAND_HEIGHTS[layer]
    cx = PAD + LAYER_LABEL_W // 2
    cy = y0 + h // 2
    color = LAYER_COLORS[layer]
    return f"""
  <g>
    <rect x="{PAD}" y="{y0}" width="{LAYER_LABEL_W}" height="{h}"
          fill="{NODE_BG}" stroke="{color}" stroke-width="2" rx="14"/>
    <rect x="{PAD}" y="{y0}" width="6" height="{h}" fill="{color}" rx="3"/>
    <text x="{cx}" y="{cy - 36}" font-family="Helvetica" font-size="13"
          font-weight="700" fill="{color}" text-anchor="middle"
          letter-spacing="2">LAYER {layer}</text>
    <text x="{cx}" y="{cy - 6}" font-family="Helvetica" font-size="22"
          font-weight="800" fill="{TITLE}" text-anchor="middle">{cn}</text>
    <text x="{cx}" y="{cy + 14}" font-family="Helvetica" font-size="12"
          fill="{DIM_LABEL}" text-anchor="middle">{en}</text>
    <text x="{cx}" y="{cy + 40}" font-family="Helvetica" font-size="10"
          fill="{DIM_LABEL}" text-anchor="middle" font-style="italic">{desc}</text>
  </g>"""


def band_bg(layer: int) -> str:
    y0 = band_y(layer)
    h = BAND_HEIGHTS[layer]
    color = LAYER_COLORS[layer]
    x = PAD + LAYER_LABEL_W + 20
    bw = CR - x
    gid = f"grad-band-{layer}"
    return f"""
  <defs>
    <linearGradient id="{gid}" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{color}" stop-opacity="0.10"/>
      <stop offset="100%" stop-color="{color}" stop-opacity="0.02"/>
    </linearGradient>
  </defs>
  <rect x="{x}" y="{y0}" width="{bw}" height="{h}"
        fill="url(#{gid})" stroke="{color}" stroke-width="1" stroke-opacity="0.35" rx="14"/>"""


CR = W - 40  # content right boundary


def flow_strip(from_layer: int, to_layer: int, label: str, sublabel: str,
               color: str, direction: str = "down") -> str:
    """Cross-layer flow indicator placed in the BAND_GAP between bands."""
    y_from = band_y(from_layer) + BAND_HEIGHTS[from_layer]
    y_to = band_y(to_layer)
    cy = (y_from + y_to) // 2
    x0 = PAD + LAYER_LABEL_W + 20
    w = CR - x0
    h = 30
    sy = cy - h // 2
    parts = [
        f'<rect x="{x0}" y="{sy}" width="{w}" height="{h}" rx="{h // 2}"'
        f' fill="{color}" fill-opacity="0.16" stroke="{color}"'
        f' stroke-opacity="0.7" stroke-width="1.4"/>',
    ]
    cx = x0 + w // 2
    for i, dx in enumerate([-30, 0, 30]):
        x = cx + dx
        if direction == "down":
            d = f"M {x-9} {sy+10} L {x} {sy+21} L {x+9} {sy+10}"
        else:
            d = f"M {x-9} {sy+21} L {x} {sy+10} L {x+9} {sy+21}"
        parts.append(
            f'<path d="{d}" stroke="{color}" stroke-width="2.6"'
            f' stroke-linecap="round" stroke-linejoin="round" fill="none"'
            f' opacity="{0.55 + i * 0.18}"/>'
        )
    parts.append(
        f'<text x="{x0 + 18}" y="{sy + h // 2 + 4}" font-family="Helvetica"'
        f' font-size="13" font-weight="800" fill="{color}">{label}</text>'
    )
    parts.append(
        f'<text x="{x0 + w - 18}" y="{sy + h // 2 + 4}" font-family="Helvetica"'
        f' font-size="11" fill="{DIM_LABEL}" text-anchor="end">{sublabel}</text>'
    )
    return "".join(parts)


def chip(x: int, y: int, slug: str, name: str,
         w: int = 96, h: int = 88, accent: str = "#475569") -> str:
    out = [
        f'<rect x="{x+2}" y="{y+2}" width="{w}" height="{h}" fill="#000" opacity="0.20" rx="9"/>',
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{NODE_BG}"'
        f' stroke="{accent}" stroke-width="1.2" rx="9"/>',
        f'<rect x="{x}" y="{y}" width="{w}" height="3" fill="{accent}" rx="1.5"/>',
    ]
    icon = img_b64(slug)
    icon_sz = 40
    if icon:
        out.append(f'<image href="{icon}" x="{x + (w-icon_sz)//2}" y="{y+12}"'
                   f' width="{icon_sz}" height="{icon_sz}"/>')
    out.append(
        f'<text x="{x + w//2}" y="{y + h - 22}" font-family="Helvetica" font-size="10.5"'
        f' font-weight="700" fill="{LABEL}" text-anchor="middle">{name}</text>'
    )
    return "".join(out)


def tool_box(x: int, y: int, w: int, h: int, slug: str, name: str,
             role: str, accent: str) -> str:
    out = [
        f'<rect x="{x+3}" y="{y+3}" width="{w}" height="{h}" fill="#000" opacity="0.25" rx="10"/>',
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{NODE_BG}"'
        f' stroke="{accent}" stroke-width="1.6" rx="10"/>',
        f'<rect x="{x}" y="{y}" width="{w}" height="4" fill="{accent}" rx="2"/>',
    ]
    icon = img_b64(slug)
    if icon:
        out.append(f'<image href="{icon}" x="{x+14}" y="{y+18}" width="48" height="48"/>')
    out.append(
        f'<text x="{x+74}" y="{y+38}" font-family="Helvetica" font-size="15"'
        f' font-weight="800" fill="{TITLE}">{name}</text>'
    )
    out.append(
        f'<text x="{x+74}" y="{y+58}" font-family="Helvetica" font-size="10"'
        f' fill="{DIM_LABEL}">{role}</text>'
    )
    return "".join(out)


def stage_arrow(x: int, y: int, w: int, h: int, idx: int,
                name: str, hint: str, color: str) -> str:
    # Arrow polygon with text positions proportional to h
    points = (f"{x},{y} {x+w-18},{y} {x+w},{y+h//2} {x+w-18},{y+h} "
              f"{x},{y+h} {x+18},{y+h//2}")
    step_y = y + max(14, h // 5)
    name_y = y + h // 2 + 4
    hint_y = y + h - 8
    return (
        f'<polygon points="{points}" fill="{NODE_BG}" stroke="{color}"'
        f' stroke-width="1.6"/>'
        f'<rect x="{x+18}" y="{y}" width="{w-36}" height="3" fill="{color}" rx="1.5"/>'
        f'<text x="{x + w//2}" y="{step_y}" font-family="Helvetica" font-size="11"'
        f' font-weight="700" fill="{color}" text-anchor="middle">STEP {idx}</text>'
        f'<text x="{x + w//2}" y="{name_y}" font-family="Helvetica" font-size="15"'
        f' font-weight="800" fill="{TITLE}" text-anchor="middle">{name}</text>'
        f'<text x="{x + w//2}" y="{hint_y}" font-family="Helvetica" font-size="9"'
        f' fill="{DIM_LABEL}" text-anchor="middle">{hint}</text>'
    )


def label_pill(x: int, y: int, text: str, color: str, w: int = 0) -> str:
    if w == 0:
        w = text_w(text, 10) + 22
    return (
        f'<rect x="{x - w//2}" y="{y - 11}" width="{w}" height="22"'
        f' fill="{BG}" stroke="{color}" stroke-width="1.2" rx="11"/>'
        f'<text x="{x}" y="{y + 4}" font-family="Helvetica" font-size="10"'
        f' font-weight="700" fill="{color}" text-anchor="middle">{text}</text>'
    )


def flow_arrow_down(x: int, y_top: int, y_bot: int, color: str,
                    label: str = "", lw: int = 0) -> str:
    out = [
        f'<path d="M {x} {y_top} L {x} {y_bot}" stroke="{color}" stroke-width="2.5"'
        f' fill="none" marker-end="url(#arrow-{color[1:]})"/>'
    ]
    if label:
        if lw == 0:
            lw = text_w(label, 10) + 22
        my = (y_top + y_bot) // 2
        out.append(label_pill(x, my, label, color, lw))
    return "".join(out)


# ── Title + subtitle ─────────────────────────────────────
def title_bar() -> str:
    return f"""
  <text x="{(CR+PAD)//2}" y="56" font-family="Helvetica" font-size="32"
        font-weight="800" fill="{TITLE}" text-anchor="middle">
    ReceptivIQ Platform — Network Diagram
  </text>
  <text x="{(CR+PAD)//2}" y="86" font-family="Helvetica" font-size="13"
        fill="{DIM_LABEL}" text-anchor="middle">
    External → ELT 8-step pipeline → 3-Lake → Core AI Brain → Pillar Agents → Portal
  </text>
  <text x="{(CR+PAD)//2}" y="108" font-family="Helvetica" font-size="11"
        fill="{DIM_LABEL}" text-anchor="middle" font-style="italic">
    Cross-cutting: GDPR · CCPA · HIPAA · SOC 2 · Per-Tenant Data Residency · PII Segregation Boundary
  </text>"""


# ── Bottom legend ────────────────────────────────────────
def legend() -> str:
    y = H - 70
    parts = [
        f'<rect x="{PAD}" y="{y}" width="{CR - PAD}" height="50"'
        f' fill="{NODE_BG}" stroke="#1F2937" stroke-width="1" rx="10"/>',
        f'<text x="{PAD + 18}" y="{y + 30}" font-family="Helvetica" font-size="11"'
        f' font-weight="700" fill="{DIM_LABEL}" letter-spacing="1.5">LEGEND ›</text>'
    ]
    items = [
        ("Data Flow", EDGE_DATA),
        ("AI Call", EDGE_AI),
        ("User Flow", EDGE_USER),
        ("Compliance Boundary", EDGE_GUARD),
        ("PII Segregation Boundary", EDGE_PII),
        ("Encryption AES-256 + TLS 1.3", "#94A3B8"),
    ]
    lx = PAD + 120
    for label, color in items:
        parts.append(
            f'<rect x="{lx}" y="{y + 16}" width="20" height="14" fill="{color}" rx="3"/>'
            f'<text x="{lx + 28}" y="{y + 28}" font-family="Helvetica" font-size="11"'
            f' fill="{LABEL}">{label}</text>'
        )
        lx += text_w(label, 11) + 70
    return "".join(parts)


# ─────────────────────────────────────────────────────────────
# Build SVG
# ─────────────────────────────────────────────────────────────
def build_svg() -> str:
    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"'
        f' viewBox="0 0 {W} {H}">'
    )
    # Background
    parts.append(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
    parts.append(
        '<defs><pattern id="dots" width="34" height="34" patternUnits="userSpaceOnUse">'
        '<circle cx="2" cy="2" r="1" fill="#1E293B"/></pattern></defs>'
        f'<rect width="{W}" height="{H}" fill="url(#dots)" opacity="0.4"/>'
    )
    # Arrow markers
    arrow_defs = '<defs>'
    for color in [EDGE_DATA, EDGE_USER, EDGE_AI, EDGE_GUARD, EDGE_PII,
                  LAYER_COLORS[1], LAYER_COLORS[2], LAYER_COLORS[3],
                  LAYER_COLORS[4], LAYER_COLORS[5], LAYER_COLORS[6], "#94A3B8"]:
        cid = color[1:]
        arrow_defs += (
            f'<marker id="arrow-{cid}" viewBox="0 0 10 10" refX="9" refY="5"'
            f' markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{color}"/></marker>'
        )
    arrow_defs += '</defs>'
    parts.append(arrow_defs)

    parts.append(title_bar())

    # Per-layer band
    for n in (1, 2, 3, 4, 5, 6):
        parts.append(band_bg(n))

    # ─────────────────────────────────────────────────
    # LAYER 1 — External Sources (14 chips + categories)
    # ─────────────────────────────────────────────────
    parts.append(layer_label(1, "External Sources", "14 Priority-1",
                             "Audience · Media · Analytics · Transfer"))
    L1_Y = band_y(1) + 14
    L1_X = PAD + LAYER_LABEL_W + 40

    # 4 category sub-titles (laid out horizontally)
    cats = [
        ("Audience / CRM",       ["experian", "transunion", "liveramp", "hubspot", "plus_more"]),
        ("Measurement",     ["nielsen", "placeriq"]),
        ("Ad Platforms",   ["dv360", "meta", "tiktok", "trade_desk", "stackadapt", "plus_more"]),
        ("Analytics / Advocacy / Transfer",       ["ga4", "quorum", "tresorit"]),
    ]

    # 12 chips across 4 categories, width allocated proportionally
    cat_widths = {0: 312, 1: 208, 2: 416, 3: 312}  # 96+8 * n - 8
    # Actual: 96*n + 8*(n-1) for n chips
    gap = 8
    chip_w, chip_h = 96, 88
    cur_x = L1_X
    cat_y = L1_Y + 6
    for i, (cat_name, slugs) in enumerate(cats):
        n_chips = len(slugs)
        block_w = chip_w * n_chips + gap * (n_chips - 1)
        # Category title
        parts.append(
            f'<rect x="{cur_x}" y="{cat_y}" width="{block_w}" height="22"'
            f' fill="{LAYER_COLORS[1]}" fill-opacity="0.12" stroke="{LAYER_COLORS[1]}"'
            f' stroke-opacity="0.5" stroke-width="1" rx="5"/>'
            f'<text x="{cur_x + block_w // 2}" y="{cat_y + 15}" font-family="Helvetica"'
            f' font-size="10" font-weight="700" fill="{LAYER_COLORS[1]}"'
            f' text-anchor="middle" letter-spacing="1">{cat_name}</text>'
        )
        # Chip row
        for j, slug in enumerate(slugs):
            cx = cur_x + j * (chip_w + gap)
            cy = cat_y + 30
            display = {
                "transunion": "TransUnion",
                "placeriq":   "Placer IQ",
                "trade_desk": "Trade Desk",
                "dv360":      "DV360",
                "ga4":        "GA4",
                "liveramp":   "LiveRamp",
                "experian":   "Experian",
                "nielsen":    "Nielsen",
                "meta":       "Meta",
                "tiktok":     "TikTok",
                "quorum":     "Quorum",
                "tresorit":   "Tresorit",
                "stackadapt": "StackAdapt",
                "plus_more":  "+More",
            }.get(slug, slug.title())
            parts.append(chip(cx, cy, slug, display, w=chip_w, h=chip_h,
                              accent=LAYER_COLORS[1]))
        cur_x += block_w + 28  # Spacing between categories

    # ─────────────────────────────────────────────────
    # LAYER 2 — ELT 8-step pipeline (Extract → Classify → Load → 5 Transforms)
    # ─────────────────────────────────────────────────
    parts.append(layer_label(2, "ELT Pipeline", "Ingestion + 8-step Transform",
                             "Orchestrator (choose one): Dagster OSS / Apache Airflow"))
    L2_Y = band_y(2) + 14
    avail_w = CR - L1_X - 20

    # ── ELT 8-step pipeline: all 8 STEPs explicitly visible ──
    # Row 1 (top): STEPs 1-3 (Extract → Classify → Load, pre-warehouse)
    # Row 2 (bottom): STEPs 4-8 (in-warehouse dbt 5-layer transform)
    sh = 70
    row_gap = 10

    # Row 1: STEPs 1-3
    stages_pre = [
        ("Extract",     "External API · 14 P1 sources",         LAYER_COLORS[2]),
        ("Classify",    "PII/PHI per-field classification",      EDGE_PII),
        ("Load",        "Write full record to Landing Lake",     "#A16207"),
    ]
    pre_w = (avail_w - 2 * 16) // 3
    for i, (name, hint, color) in enumerate(stages_pre):
        sx = L1_X + i * (pre_w + 16)
        parts.append(stage_arrow(sx, L2_Y, pre_w, sh, i + 1, name, hint, color))

    # Row 2: STEPs 4-8
    stage_y = L2_Y + sh + row_gap
    stages_post = [
        ("Normalize",   "Field standardize (dbt)",   LAYER_COLORS[2]),
        ("Deduplicate", "Cross-platform dedup (dbt)",LAYER_COLORS[2]),
        ("Validate",    "Schema + PHI scan",         EDGE_PII),
        ("Enrich",      "JOIN + 3rd-party (dbt)",    LAYER_COLORS[2]),
        ("Index",       "Vector + materialized view",LAYER_COLORS[2]),
    ]
    stage_w = (avail_w - 4 * 16) // 5
    for i, (name, hint, color) in enumerate(stages_post):
        sx = L1_X + i * (stage_w + 16)
        # STEPs 4-8
        parts.append(stage_arrow(sx, stage_y, stage_w, sh, i + 4, name, hint, color))

    # Orchestration strip (Dagster OSS / Airflow — choose one + Step Functions aux)
    orch_y = stage_y + sh + 8
    orch_h = 36
    dag_color = "#4F43DC"
    afw_color = "#017CEE"
    sfn_color = "#F59E0B"
    parts.append(
        f'<rect x="{L1_X}" y="{orch_y}" width="{avail_w}" height="{orch_h}"'
        f' fill="{NODE_BG_2}" stroke="{dag_color}" stroke-width="1.4" rx="8"/>'
        f'<rect x="{L1_X}" y="{orch_y}" width="6" height="{orch_h}" fill="{dag_color}" rx="3"/>'
        f'<text x="{L1_X + 18}" y="{orch_y + 15}" font-family="Helvetica" font-size="10"'
        f' font-weight="800" fill="{dag_color}" letter-spacing="1.4">ORCHESTRATION · CHOOSE ONE</text>'
        f'<text x="{L1_X + 18}" y="{orch_y + 30}" font-family="Helvetica" font-size="11"'
        f' font-weight="700" fill="{TITLE}">🟪 Dagster OSS</text>'
        f'<text x="{L1_X + 130}" y="{orch_y + 30}" font-family="Helvetica" font-size="9"'
        f' fill="{DIM_LABEL}">Asset Graph · dagster-dbt · per-Agency Partition</text>'
        f'<text x="{L1_X + 380}" y="{orch_y + 30}" font-family="Helvetica" font-size="13"'
        f' font-weight="800" fill="{DIM_LABEL}">|</text>'
        f'<text x="{L1_X + 395}" y="{orch_y + 30}" font-family="Helvetica" font-size="11"'
        f' font-weight="700" fill="{afw_color}">🟦 Apache Airflow</text>'
        f'<text x="{L1_X + 510}" y="{orch_y + 30}" font-family="Helvetica" font-size="9"'
        f' fill="{DIM_LABEL}">1000+ Providers · team familiar · DAG model</text>'
        f'<rect x="{L1_X + avail_w - 240}" y="{orch_y + 6}" width="232" height="{orch_h - 12}"'
        f' fill="{NODE_BG}" stroke="{sfn_color}" stroke-width="1" rx="6"/>'
        f'<text x="{L1_X + avail_w - 229}" y="{orch_y + 21}" font-family="Helvetica" font-size="10"'
        f' font-weight="700" fill="{sfn_color}">🟧 AWS Step Functions</text>'
        f'<text x="{L1_X + avail_w - 229}" y="{orch_y + 31}" font-family="Helvetica" font-size="9"'
        f' fill="{DIM_LABEL}">AI write-back approval · DSAR long flow</text>'
    )

    # ─────────────────────────────────────────────────
    # LAYER 3 — 3-Lake Warehouse (Landing → Raw PII → Processed)
    # ─────────────────────────────────────────────────
    parts.append(layer_label(3, "3-Lake Warehouse", "on Neon Postgres",
                             "Landing → 🔴 Raw PII → 🟢 Processed"))
    L3_Y = band_y(3) + 18
    L3_H = BAND_HEIGHTS[3] - 36
    avail_w3 = CR - L1_X - 20
    BRONZE_NW = "#A16207"
    inter_gap_nw = 14
    pii_boundary_gap_nw = 60
    lake_w = (avail_w3 - inter_gap_nw - pii_boundary_gap_nw - 26) // 3

    landing_x_nw = L1_X
    raw_x_nw = landing_x_nw + lake_w + inter_gap_nw
    pii_x_center = raw_x_nw + lake_w + (pii_boundary_gap_nw // 2)
    proc_x = pii_x_center + (pii_boundary_gap_nw // 2)

    # ── ⬛ Landing Lake (Bronze) ──────────────────────────
    parts.append(
        f'<rect x="{landing_x_nw}" y="{L3_Y}" width="{lake_w}" height="{L3_H}"'
        f' fill="{BRONZE_NW}" fill-opacity="0.08" stroke="{BRONZE_NW}"'
        f' stroke-width="2" rx="14"/>'
        f'<rect x="{landing_x_nw}" y="{L3_Y}" width="{lake_w}" height="6"'
        f' fill="{BRONZE_NW}" rx="3"/>'
    )
    _bcx_nw = landing_x_nw + lake_w // 2
    _bbx_nw = _bcx_nw - 110
    _bby_nw = L3_Y + 22
    parts.append(
        f'<rect x="{_bbx_nw - 7}" y="{_bby_nw}" width="14" height="11" fill="{BRONZE_NW}" rx="1.5"/>'
        f'<rect x="{_bbx_nw - 7}" y="{_bby_nw + 4.5}" width="14" height="1.5" fill="{BG}"/>'
        f'<rect x="{_bbx_nw - 0.5}" y="{_bby_nw}" width="1.5" height="4.5" fill="{BG}"/>'
        f'<rect x="{_bbx_nw - 0.5}" y="{_bby_nw + 6}" width="1.5" height="5" fill="{BG}"/>'
        f'<text x="{_bcx_nw + 10}" y="{L3_Y + 30}" font-family="Helvetica"'
        f' font-size="17" font-weight="800" fill="{BRONZE_NW}" text-anchor="middle">'
        f'Landing Lake (Bronze)</text>'
        f'<text x="{_bcx_nw}" y="{L3_Y + 50}" font-family="Helvetica"'
        f' font-size="11" fill="{LABEL}" text-anchor="middle">Full record · immutable · ELT + auditors</text>'
        f'<text x="{_bcx_nw}" y="{L3_Y + 68}" font-family="Helvetica"'
        f' font-size="10" font-weight="800" fill="{BRONZE_NW}" text-anchor="middle"'
        f' letter-spacing="1.4">STAGE 1: raw data landing zone</text>'
    )
    landing_tables_nw = [
        ("landing.&lt;source&gt;_records", "Full record · PII cols encrypted"),
        ("landing.sync_state",           "cursor / watermark state"),
    ]
    l_table_x = landing_x_nw + 16
    l_table_w = lake_w - 32
    for i, (tname, sub) in enumerate(landing_tables_nw):
        ty = L3_Y + 80 + i * 38
        parts.append(
            f'<rect x="{l_table_x}" y="{ty}" width="{l_table_w}" height="32"'
            f' fill="{NODE_BG_2}" stroke="{BRONZE_NW}" stroke-width="1.4" rx="7"/>'
            f'<rect x="{l_table_x}" y="{ty}" width="3" height="32" fill="{BRONZE_NW}" rx="1.5"/>'
            f'<text x="{l_table_x + 12}" y="{ty + 14}" font-family="Menlo,Helvetica"'
            f' font-size="10" font-weight="800" fill="{BRONZE_NW}">{tname}</text>'
            f'<text x="{l_table_x + 12}" y="{ty + 27}" font-family="Helvetica"'
            f' font-size="9" fill="{DIM_LABEL}">{sub}</text>'
        )
    parts.append(
        f'<text x="{_bcx_nw}" y="{L3_Y + 80 + 2 * 38 + 16}" font-family="Helvetica"'
        f' font-size="9.5" font-weight="700" fill="{BRONZE_NW}" text-anchor="middle">'
        f'⚠ Business/AI forbidden · HIPAA 6y / non-HIPAA 90d</text>'
    )

    # ── ⬛ ↔ 🔴 soft divider (same PII trust boundary) ─────
    inter_x_nw = raw_x_nw - inter_gap_nw // 2
    parts.append(
        f'<line x1="{inter_x_nw}" y1="{L3_Y + 14}" x2="{inter_x_nw}" y2="{L3_Y + L3_H - 14}"'
        f' stroke="{BRONZE_NW}" stroke-width="1.4" stroke-dasharray="3 4" opacity="0.55"/>'
        f'<text x="{inter_x_nw}" y="{L3_Y + L3_H // 2}" font-family="Helvetica"'
        f' font-size="9" fill="{DIM_LABEL}" text-anchor="middle" opacity="0.8">same PII zone</text>'
    )

    # ── 🔴 Raw PII Lake ─────────────────────────────────────
    parts.append(
        f'<rect x="{raw_x_nw}" y="{L3_Y}" width="{lake_w}" height="{L3_H}"'
        f' fill="{EDGE_PII}" fill-opacity="0.08" stroke="{EDGE_PII}"'
        f' stroke-width="2" rx="14"/>'
        f'<rect x="{raw_x_nw}" y="{L3_Y}" width="{lake_w}" height="6"'
        f' fill="{EDGE_PII}" rx="3"/>'
    )
    _cx = raw_x_nw + lake_w // 2
    _lx = _cx - 116
    _ly = L3_Y + 22
    parts.append(
        f'<rect x="{_lx - 7}" y="{_ly}" width="14" height="12" fill="{EDGE_PII}" rx="2"/>'
        f'<path d="M {_lx - 4} {_ly + 1} L {_lx - 4} {_ly - 5} A 4 4 0 0 1 {_lx + 4} {_ly - 5} L {_lx + 4} {_ly + 1}"'
        f' stroke="{EDGE_PII}" stroke-width="2" fill="none"/>'
        f'<text x="{_cx + 10}" y="{L3_Y + 30}" font-family="Helvetica"'
        f' font-size="17" font-weight="800" fill="{EDGE_PII}" text-anchor="middle">'
        f'Raw PII-Segregated Lake</text>'
        f'<text x="{_cx}" y="{L3_Y + 50}" font-family="Helvetica"'
        f' font-size="11" fill="{LABEL}" text-anchor="middle">PII fields only · PII Access Service egress</text>'
        f'<text x="{_cx}" y="{L3_Y + 68}" font-family="Helvetica"'
        f' font-size="10" font-weight="800" fill="{EDGE_PII}" text-anchor="middle"'
        f' letter-spacing="1.4">STAGE 3 derive A: PII fields</text>'
    )
    raw_tables = [
        ("raw_secure.users",              "Subject dim · email/phone enc"),
        ("raw_secure.&lt;source&gt;_pii", "PII columns · record_id linked"),
        ("raw_secure.pii_access_log",     "PII Access Service egress audit"),
    ]
    r_table_x = raw_x_nw + 16
    r_table_w = lake_w - 32
    for i, (tname, sub) in enumerate(raw_tables):
        ty = L3_Y + 80 + i * 28
        parts.append(
            f'<rect x="{r_table_x}" y="{ty}" width="{r_table_w}" height="24"'
            f' fill="{NODE_BG_2}" stroke="{EDGE_PII}" stroke-width="1.4" rx="6"/>'
            f'<rect x="{r_table_x}" y="{ty}" width="3" height="24" fill="{EDGE_PII}" rx="1.5"/>'
            f'<text x="{r_table_x + 10}" y="{ty + 11}" font-family="Menlo,Helvetica"'
            f' font-size="9.5" font-weight="800" fill="{EDGE_PII}">{tname}</text>'
            f'<text x="{r_table_x + 10}" y="{ty + 21}" font-family="Helvetica"'
            f' font-size="8.5" fill="{DIM_LABEL}">{sub}</text>'
        )
    parts.append(
        f'<text x="{_cx}" y="{L3_Y + 80 + 3 * 28 + 14}" font-family="Helvetica"'
        f' font-size="9.5" font-weight="700" fill="{EDGE_PII}" text-anchor="middle">'
        f'🔐 AES-256 + per-Agency KMS · HIPAA 6y</text>'
    )

    # ── PII Boundary (between Raw PII and Processed only) ───
    pii_x = pii_x_center
    parts.append(
        f'<line x1="{pii_x}" y1="{L3_Y - 6}" x2="{pii_x}" y2="{L3_Y + L3_H + 6}"'
        f' stroke="{EDGE_PII}" stroke-width="3.5" stroke-dasharray="14 6"/>'
    )
    parts.append(
        f'<rect x="{pii_x - 26}" y="{L3_Y + L3_H // 2 - 32}" width="52" height="64"'
        f' fill="{BG}" stroke="{EDGE_PII}" stroke-width="2.4" rx="10"/>'
        f'<text x="{pii_x}" y="{L3_Y + L3_H // 2 - 8}" font-family="Helvetica"'
        f' font-size="26" text-anchor="middle">🔐</text>'
        f'<text x="{pii_x}" y="{L3_Y + L3_H // 2 + 14}" font-family="Helvetica"'
        f' font-size="9" font-weight="800" fill="{EDGE_PII}" text-anchor="middle">PII</text>'
        f'<text x="{pii_x}" y="{L3_Y + L3_H // 2 + 24}" font-family="Helvetica"'
        f' font-size="9" font-weight="800" fill="{EDGE_PII}" text-anchor="middle">BOUNDARY</text>'
    )

    # Right: Processed Lake
    parts.append(
        f'<rect x="{proc_x}" y="{L3_Y}" width="{lake_w}" height="{L3_H}"'
        f' fill="{LAYER_COLORS[3]}" fill-opacity="0.10" stroke="{LAYER_COLORS[3]}"'
        f' stroke-width="2" rx="14"/>'
    )
    parts.append(
        f'<rect x="{proc_x}" y="{L3_Y}" width="{lake_w}" height="6"'
        f' fill="{LAYER_COLORS[3]}" rx="3"/>'
    )
    parts.append(
        f'<text x="{proc_x + lake_w // 2}" y="{L3_Y + 30}" font-family="Helvetica"'
        f' font-size="17" font-weight="800" fill="{LAYER_COLORS[3]}" text-anchor="middle">'
        f'✓ Processed Lake</text>'
        f'<text x="{proc_x + lake_w // 2}" y="{L3_Y + 50}" font-family="Helvetica"'
        f' font-size="11" fill="{LABEL}" text-anchor="middle">Anonymized · business-ready · no plaintext PII</text>'
    )
    parts.append(
        f'<text x="{proc_x + lake_w // 2}" y="{L3_Y + 68}" font-family="Helvetica"'
        f' font-size="10" font-weight="800" fill="{LAYER_COLORS[3]}" text-anchor="middle"'
        f' letter-spacing="1.4">STAGE 3 derive B + STAGE 4 dbt 5 layers</text>'
    )
    proc_layers = [
        ("📥 raw.&lt;source&gt;",  "non-PII raw · pii_token · STAGE 1"),
        ("📦 staging",      "dbt staging · 30d"),
        ("🧱 canonical",    "13 standard entities · 3y"),
        ("📊 marts",        "business aggregates · 3-7y"),
        ("🧠 ai_context",   "AI retrieval · vector + summary · 1y"),
    ]
    proc_x_inner = proc_x + 24
    proc_w_inner = lake_w - 48
    proc_h_each = 20
    proc_gap = 3
    proc_y_start = L3_Y + 80
    for i, (name, desc) in enumerate(proc_layers):
        ly = proc_y_start + i * (proc_h_each + proc_gap)
        parts.append(
            f'<rect x="{proc_x_inner}" y="{ly}" width="{proc_w_inner}" height="{proc_h_each}"'
            f' fill="{NODE_BG_2}" stroke="{LAYER_COLORS[3]}" stroke-width="1.3" rx="6"/>'
            f'<rect x="{proc_x_inner}" y="{ly}" width="3" height="{proc_h_each}"'
            f' fill="{LAYER_COLORS[3]}" rx="1.5"/>'
            f'<text x="{proc_x_inner + 12}" y="{ly + 16}" font-family="Menlo,Helvetica"'
            f' font-size="11" font-weight="800" fill="{LAYER_COLORS[3]}">{name}</text>'
            f'<text x="{proc_x_inner + proc_w_inner - 10}" y="{ly + 16}" font-family="Helvetica"'
            f' font-size="9" fill="{DIM_LABEL}" text-anchor="end">{desc}</text>'
        )
        if i < len(proc_layers) - 1:
            ax = proc_x + lake_w // 2
            ay = ly + proc_h_each + 1
            parts.append(
                f'<path d="M {ax - 5} {ay} L {ax} {ay + 3} L {ax + 5} {ay}"'
                f' stroke="{LAYER_COLORS[3]}" stroke-width="1.8"'
                f' stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
            )
    # Neon icon (warehouse choice)
    sf_icon = img_b64("neon")
    if sf_icon:
        parts.append(
            f'<image href="{sf_icon}" x="{CR - 60}" y="{L3_Y + 4}" width="36" height="36"/>'
            f'<text x="{CR - 42}" y="{L3_Y + 54}" font-family="Helvetica" font-size="9"'
            f' fill="{DIM_LABEL}" text-anchor="middle">Neon Postgres</text>'
        )

    # Tokenized join arrow — secure link from Raw Lake to Processed Lake
    tj_y = L3_Y + L3_H - 20
    tj_x1 = raw_x_nw + lake_w - 14
    tj_x2 = proc_x + 14
    parts.append(
        f'<path d="M {tj_x1} {tj_y} Q {pii_x} {tj_y + 12} {tj_x2} {tj_y}"'
        f' stroke="{EDGE_DATA}" stroke-width="2" fill="none" stroke-dasharray="6 4"'
        f' marker-end="url(#arrow-{EDGE_DATA[1:]})"/>'
        f'<rect x="{pii_x - 84}" y="{tj_y + 14}" width="168" height="20"'
        f' fill="{BG}" stroke="{EDGE_DATA}" stroke-width="1.2" rx="10"/>'
        f'<text x="{pii_x}" y="{tj_y + 28}" font-family="Helvetica" font-size="10"'
        f' font-weight="700" fill="{EDGE_DATA}" text-anchor="middle">'
        f'🔗 Hashed / Tokenized Join Key</text>'
    )

    # ─────────────────────────────────────────────────
    # LAYER 4 — Core AI Brain (6 core components)
    # ─────────────────────────────────────────────────
    parts.append(layer_label(4, "Core AI Brain", "6 Components",
                             "Context · Router · Orchestrator"))
    L4_Y = band_y(4) + 18
    L4_H = BAND_HEIGHTS[4] - 36
    brain_components = [
        ("Context Builder",  "brain",      "tenant/role/PII-safe"),
        ("LLM Router",       "openrouter", "model · cost · compliance"),
        ("Agent Orchestrator","attribution","serial/parallel 4 agents"),
        ("Tool Executor",    "fastapi",    "read/write · approval gate"),
        ("Memory · Retrieval","persona",   "summary + vector"),
        ("Audit · Cost",     "compliance", "prompt · token · audit"),
    ]
    cw_brain = (avail_w3 - 5 * 12) // 6
    ch_brain = L4_H
    for i, (name, slug, role) in enumerate(brain_components):
        bx = L1_X + i * (cw_brain + 12)
        parts.append(
            f'<rect x="{bx+2}" y="{L4_Y+2}" width="{cw_brain}" height="{ch_brain}"'
            f' fill="#000" opacity="0.25" rx="10"/>'
            f'<rect x="{bx}" y="{L4_Y}" width="{cw_brain}" height="{ch_brain}"'
            f' fill="{NODE_BG}" stroke="{LAYER_COLORS[4]}" stroke-width="1.5" rx="10"/>'
            f'<rect x="{bx}" y="{L4_Y}" width="{cw_brain}" height="4" fill="{LAYER_COLORS[4]}" rx="2"/>'
        )
        ic = img_b64(slug)
        if ic:
            icon_sz = 72
            parts.append(
                f'<image href="{ic}" x="{bx + cw_brain // 2 - icon_sz // 2}" y="{L4_Y + 28}"'
                f' width="{icon_sz}" height="{icon_sz}"/>'
            )
        parts.append(
            f'<text x="{bx + cw_brain // 2}" y="{L4_Y + ch_brain - 36}" font-family="Helvetica"'
            f' font-size="13" font-weight="800" fill="{TITLE}" text-anchor="middle">{name}</text>'
            f'<text x="{bx + cw_brain // 2}" y="{L4_Y + ch_brain - 18}" font-family="Helvetica"'
            f' font-size="9.5" fill="{DIM_LABEL}" text-anchor="middle">{role}</text>'
        )

    # ─────────────────────────────────────────────────
    # LAYER 5 — 4 Pillar Agents
    # ─────────────────────────────────────────────────
    parts.append(layer_label(5, "Pillar Agents", "4 Pillar AI Agents",
                             "Persona · Creative · Attribution · Media"))
    L5_Y = band_y(5) + 18
    agent_w = (avail_w3 - 3 * 24) // 4
    agent_h = 140
    agents = [
        ("Persona Agent", "persona", "Audience profiling", "Claude Opus 4.7"),
        ("Creative Agent", "creatives", "Ad creative gen", "Claude Sonnet 4.6"),
        ("Attribution Agent", "attribution", "Cross-channel attr", "Claude Sonnet 4.6"),
        ("Media Agent ★", "audience", "Media buying optim", "Claude Sonnet 4.6"),
    ]
    for i, (name, slug, role, model) in enumerate(agents):
        ax = L1_X + i * (agent_w + 24)
        out = [
            f'<rect x="{ax+3}" y="{L5_Y+3}" width="{agent_w}" height="{agent_h}"'
            f' fill="#000" opacity="0.25" rx="12"/>',
            f'<rect x="{ax}" y="{L5_Y}" width="{agent_w}" height="{agent_h}"'
            f' fill="{NODE_BG}" stroke="{LAYER_COLORS[5]}" stroke-width="1.8" rx="12"/>',
            f'<rect x="{ax}" y="{L5_Y}" width="{agent_w}" height="5"'
            f' fill="{LAYER_COLORS[5]}" rx="2.5"/>',
        ]
        ic = img_b64(slug)
        if ic:
            out.append(f'<image href="{ic}" x="{ax + agent_w // 2 - 24}"'
                       f' y="{L5_Y + 16}" width="48" height="48"/>')
        out.append(
            f'<text x="{ax + agent_w // 2}" y="{L5_Y + 86}" font-family="Helvetica"'
            f' font-size="14" font-weight="800" fill="{TITLE}" text-anchor="middle">'
            f'{name}</text>'
        )
        out.append(
            f'<text x="{ax + agent_w // 2}" y="{L5_Y + 104}" font-family="Helvetica"'
            f' font-size="10" fill="{LABEL}" text-anchor="middle">{role}</text>'
        )
        out.append(
            f'<text x="{ax + agent_w // 2}" y="{L5_Y + 122}" font-family="Helvetica"'
            f' font-size="9" fill="{DIM_LABEL}" text-anchor="middle">{model}</text>'
        )
        parts.append("".join(out))

    # ─────────────────────────────────────────────────
    # LAYER 6 — Apps / client portal
    # ─────────────────────────────────────────────────
    parts.append(layer_label(6, "Application / Portal", "4 User Types",
                             "White-labeled · real-time"))
    L6_Y = band_y(6) + 22
    portal_items = [
        ("Platform Super Admin", "fastapi", "L1 · cross-Agency aggregates"),
        ("Agency Admin",         "auth",    "L2 · all Clients in Agency"),
        ("Agency Operator",      "dashboard","L2 · Agency daily workflows"),
        ("Client Viewer",        "portal",  "L3 · own Client data (RLS)"),
    ]
    pw = (avail_w3 - 3 * 22) // 4
    ph = BAND_HEIGHTS[6] - 48
    for i, (name, slug, role) in enumerate(portal_items):
        px = L1_X + i * (pw + 22)
        parts.append(tool_box(px, L6_Y, pw, ph, slug, name, role, LAYER_COLORS[6]))

    # ─────────────────────────────────────────────────
    # (old band-gap arrows replaced by flow_strip at end of file)
    # ─────────────────────────────────────────────────
    # Outer compliance boundary (amber dashed border + top banner)
    # ─────────────────────────────────────────────────
    comp_top = band_y(1) - 18
    comp_bot = band_y(6) + BAND_HEIGHTS[6] + 16
    parts.append(
        f'<rect x="{PAD - 8}" y="{comp_top}" width="{CR - PAD + 16}"'
        f' height="{comp_bot - comp_top}" fill="none" stroke="{EDGE_GUARD}"'
        f' stroke-width="2.5" stroke-dasharray="12 8" rx="20" opacity="0.7"/>'
    )
    banner_w = 600
    bx = PAD - 8 + (CR - PAD + 16 - banner_w) // 2
    parts.append(
        f'<rect x="{bx}" y="{comp_top - 16}" width="{banner_w}" height="32"'
        f' fill="{BG}" stroke="{EDGE_GUARD}" stroke-width="2" rx="16"/>'
        f'<text x="{bx + banner_w // 2}" y="{comp_top + 5}" font-family="Helvetica"'
        f' font-size="13" font-weight="800" fill="{EDGE_GUARD}" text-anchor="middle">'
        f'🛡 COMPLIANCE BOUNDARY · GDPR · CCPA · HIPAA · SOC 2 · Per-Tenant Data Residency</text>'
    )

    # Inter-band flow strips (5 · turns "components in a row" into an end-to-end flow)
    parts.append(flow_strip(
        1, 2, "① Extract",
        "TLS 1.3 + OAuth · per-source Credential Vault · 14 P1 sources",
        LAYER_COLORS[2]))
    parts.append(flow_strip(
        2, 3, "② Classify · Transform · Load",
        "raw_pii → Raw Lake (isolated) · staging / canonical → Processed Lake",
        LAYER_COLORS[3]))
    parts.append(flow_strip(
        3, 4, "③ PII-safe Context Retrieval",
        "AI reads Processed Lake only · never touches plaintext PII · gated via PII Access Service",
        LAYER_COLORS[4]))
    parts.append(flow_strip(
        4, 5, "④ Agent Orchestrate",
        "LLM Router · token budgets · serial / parallel 4 agents · Langfuse traces",
        LAYER_COLORS[5]))
    parts.append(flow_strip(
        5, 6, "⑤ Deliver",
        "Persona / Creative / Attribution / Media outputs → Agency · Client portals",
        LAYER_COLORS[6]))

    parts.append(legend())
    parts.append('</svg>')
    return "\n".join(parts)


def main() -> None:
    svg = build_svg()
    OUT_DIR.mkdir(exist_ok=True, parents=True)
    out_svg = OUT_DIR / "network-diagram-en.svg"
    out_svg.write_text(svg)
    print(f"✓ wrote {out_svg} ({len(svg):,} bytes)")
    out_png = OUT_DIR / "network-diagram-en.png"
    try:
        subprocess.run(
            ["rsvg-convert", str(out_svg), "-o", str(out_png), "-w", str(W)],
            check=True, capture_output=True
        )
        print(f"✓ wrote {out_png} via rsvg-convert")
    except FileNotFoundError:
        print("rsvg-convert not found; PNG skipped")
    except subprocess.CalledProcessError as e:
        print(f"rsvg-convert failed: {e.stderr.decode()}")


if __name__ == "__main__":
    main()
