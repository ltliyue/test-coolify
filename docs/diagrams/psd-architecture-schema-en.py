#!/usr/bin/env python3
"""ReceptivIQ PSD · Architecture Solution Schema (English)

7-layer end-to-end architecture from client portal to infrastructure:
  L1 Client / Agency Portal
  L2 Functional Pillars (MVP · 5 modules)
  L3 Core AI Brain (6 components + 4 Pillar Agents)
  L4 ELT Transform Pipeline (5 in-warehouse stages)
  L5 Two-Lake Warehouse on Neon Postgres (6 schemas)
  L6 External Data Sources (Priority 1, 11 + extensible)
  L7 Infrastructure · Cross-Cutting

Right side: Compliance panel (spine + per-layer anchor lines)
Bottom: Key Constraints bar

Output: docs/psd/architecture-schema-en.{svg, png}
"""
from __future__ import annotations
import base64
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
ICONS = ROOT / "icons"
OUT_DIR = ROOT.parent / "psd"

# Theme ──────────────────────────────────────────────────
BG          = "#0B1220"
NODE_BG     = "#111B2D"
NODE_BG_2   = "#0F1729"
TITLE       = "#F8FAFC"
LABEL       = "#E2E8F0"
DIM_LABEL   = "#94A3B8"
EDGE_GUARD  = "#F59E0B"
EDGE_PII    = "#EF4444"

LAYER_COLORS = {
    1: "#06B6D4",   # Portal — cyan
    2: "#10B981",   # Pillars — emerald
    3: "#EC4899",   # AI Brain — pink
    4: "#3B82F6",   # ELT — blue
    5: "#8B5CF6",   # Warehouse — violet
    6: "#0EA5E9",   # Sources — sky
    7: "#EF4444",   # Infra — red
}

W, H = 2400, 2280
PAD = 40
LAYER_LABEL_W = 220
CR = 1980        # content right boundary (~380 reserved on right for Compliance Panel)

BAND_TOP = 170
BAND_GAP = 40  # widened to host inter-layer flow strips
BAND_HEIGHTS = {1: 150, 2: 180, 3: 270, 4: 170, 5: 490, 6: 230, 7: 200}
# L5 grown to 490: top ~190 for Two-Lake; bottom ~280 for the Data Lifecycle ribbon (incl. DEDUP strip)


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
    <text x="{cx}" y="{cy - 30}" font-family="Helvetica" font-size="13"
          font-weight="700" fill="{color}" text-anchor="middle"
          letter-spacing="2">LAYER {layer}</text>
    <text x="{cx}" y="{cy - 2}" font-family="Helvetica" font-size="20"
          font-weight="800" fill="{TITLE}" text-anchor="middle">{cn}</text>
    <text x="{cx}" y="{cy + 16}" font-family="Helvetica" font-size="11"
          fill="{DIM_LABEL}" text-anchor="middle">{en}</text>
    <text x="{cx}" y="{cy + 38}" font-family="Helvetica" font-size="10"
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


def flow_strip(from_layer: int, to_layer: int, label: str, sublabel: str,
               color: str, direction: str = "down") -> str:
    """Cross-layer flow indicator placed in the BAND_GAP between bands."""
    y_from = band_y(from_layer) + BAND_HEIGHTS[from_layer]
    y_to = band_y(to_layer)
    cy = (y_from + y_to) // 2
    x0 = PAD + LAYER_LABEL_W + 40
    w = CR - x0 - 10
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
        out.append(f'<image href="{icon}" x="{x+14}" y="{y+16}" width="44" height="44"/>')
    out.append(
        f'<text x="{x+70}" y="{y+34}" font-family="Helvetica" font-size="14"'
        f' font-weight="800" fill="{TITLE}">{name}</text>'
    )
    out.append(
        f'<text x="{x+70}" y="{y+52}" font-family="Helvetica" font-size="10"'
        f' fill="{DIM_LABEL}">{role}</text>'
    )
    return "".join(out)


def small_chip(x: int, y: int, slug: str, name: str,
               w: int = 96, h: int = 72, accent: str = "#475569") -> str:
    out = [
        f'<rect x="{x+2}" y="{y+2}" width="{w}" height="{h}" fill="#000" opacity="0.18" rx="8"/>',
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{NODE_BG}"'
        f' stroke="{accent}" stroke-width="1.2" rx="8"/>',
    ]
    icon = img_b64(slug)
    if icon:
        out.append(f'<image href="{icon}" x="{x + (w-32)//2}" y="{y+8}"'
                   f' width="32" height="32"/>')
    out.append(
        f'<text x="{x + w//2}" y="{y + h - 10}" font-family="Helvetica" font-size="10"'
        f' font-weight="600" fill="{LABEL}" text-anchor="middle">{name}</text>'
    )
    return "".join(out)


def section_title(x: int, y: int, text: str, color: str) -> str:
    return (f'<text x="{x}" y="{y}" font-family="Helvetica" font-size="11"'
            f' font-weight="800" fill="{color}" letter-spacing="1.6">{text}</text>')


def title_bar() -> str:
    return f"""
  <text x="{(CR+PAD)//2}" y="56" font-family="Helvetica" font-size="32"
        font-weight="800" fill="{TITLE}" text-anchor="middle">
    ReceptivIQ Platform — Architecture Solution Schema
  </text>
  <text x="{(CR+PAD)//2}" y="88" font-family="Helvetica" font-size="13"
        fill="{DIM_LABEL}" text-anchor="middle">
    7-Layer End-to-End View · MVP 5 Pillars · 4 AI Agents · Two-Lake on Neon Postgres · 14 P1 Integrations
  </text>
  <text x="{(CR+PAD)//2}" y="110" font-family="Helvetica" font-size="11"
        fill="{DIM_LABEL}" text-anchor="middle" font-style="italic">
    Top-down: Portal → Pillars → AI Brain → ELT → Two-Lake → Sources → Infrastructure
  </text>"""


# ─────────────────────────────────────────────────────────────
def build_svg() -> str:
    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"'
        f' viewBox="0 0 {W} {H}">'
    )
    parts.append(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
    parts.append(
        '<defs><pattern id="dots" width="34" height="34" patternUnits="userSpaceOnUse">'
        '<circle cx="2" cy="2" r="1" fill="#1E293B"/></pattern></defs>'
        f'<rect width="{W}" height="{H}" fill="url(#dots)" opacity="0.4"/>'
    )
    # arrow markers
    arrow_defs = '<defs>'
    for color in [EDGE_GUARD, EDGE_PII] + list(LAYER_COLORS.values()):
        cid = color[1:]
        arrow_defs += (
            f'<marker id="arrow-{cid}" viewBox="0 0 10 10" refX="9" refY="5"'
            f' markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{color}"/></marker>'
        )
    arrow_defs += '</defs>'
    parts.append(arrow_defs)

    parts.append(title_bar())

    for n in range(1, 8):
        parts.append(band_bg(n))
        # layer labels added in each layer below

    L_X = PAD + LAYER_LABEL_W + 40
    L_W = CR - L_X - 10

    # ── LAYER 1 — Portal（4 user types）────────────────────
    parts.append(layer_label(1, "Client / Portal", "Front Door · 4 User Types",
                             "White-labeled"))
    L1_Y = band_y(1) + 18
    L1_H = BAND_HEIGHTS[1] - 36
    portal_items = [
        ("Platform Super Admin", "fastapi", "L1 · cross-Agency aggregates"),
        ("Agency Admin",         "auth",      "L2 · all Clients in Agency"),
        ("Agency Operator",      "dashboard", "L2 · Agency daily workflows"),
        ("Client Viewer",        "portal",    "L3 · own Client data (RLS)"),
    ]
    pw = (L_W - 3 * 22) // 4
    for i, (n, s, r) in enumerate(portal_items):
        px = L_X + i * (pw + 22)
        parts.append(tool_box(px, L1_Y, pw, L1_H, s, n, r, LAYER_COLORS[1]))

    # ── LAYER 2 — Functional Pillars ──────────────────────
    parts.append(layer_label(2, "Functional Pillars", "MVP Scope (5 modules)",
                             "Core business pillars"))
    L2_Y = band_y(2) + 22
    L2_H = BAND_HEIGHTS[2] - 44
    pillars = [
        ("Market Research", "persona",    "Audience profile + insight"),
        ("Creative Engine", "creatives",  "Creative gen / A/B"),
        ("Media Buying",    "googleads",  "Cross-platform buying"),
        ("Attribution",     "attribution","Cross-channel attr / ROI"),
        ("Client Portal",   "portal",     "Client-facing delivery"),
    ]
    pw2 = (L_W - 4 * 16) // 5
    for i, (n, s, r) in enumerate(pillars):
        px = L_X + i * (pw2 + 16)
        parts.append(tool_box(px, L2_Y, pw2, L2_H, s, n, r, LAYER_COLORS[2]))

    # ── LAYER 3 — Core AI Brain (6 components + 4 Pillar Agents) ──
    parts.append(layer_label(3, "Core AI Brain", "6 Components + 4 Agents",
                             "Token · Langfuse · Audit"))
    L3_Y = band_y(3) + 14

    # Top row: 6 core components
    top_h = 96
    comp_w = (L_W - 5 * 10) // 6
    components = [
        ("Context Builder",   "brain",       "tenant/role/PII-safe"),
        ("LLM Router",        "openrouter",  "model · cost · compliance"),
        ("Agent Orchestrator","attribution", "serial/parallel 4 agents"),
        ("Tool Executor",     "fastapi",     "read/write · approval gate"),
        ("Memory · Retrieval","persona",     "summary + vector"),
        ("Audit · Cost",      "compliance",  "prompt · token · audit"),
    ]
    for i, (name, slug, role) in enumerate(components):
        cx = L_X + i * (comp_w + 10)
        parts.append(
            f'<rect x="{cx+2}" y="{L3_Y+2}" width="{comp_w}" height="{top_h}"'
            f' fill="#000" opacity="0.25" rx="9"/>'
            f'<rect x="{cx}" y="{L3_Y}" width="{comp_w}" height="{top_h}"'
            f' fill="{NODE_BG}" stroke="{LAYER_COLORS[3]}" stroke-width="1.4" rx="9"/>'
            f'<rect x="{cx}" y="{L3_Y}" width="{comp_w}" height="3" fill="{LAYER_COLORS[3]}" rx="1.5"/>'
        )
        ic = img_b64(slug)
        if ic:
            parts.append(
                f'<image href="{ic}" x="{cx + comp_w // 2 - 16}" y="{L3_Y + 12}"'
                f' width="32" height="32"/>'
            )
        parts.append(
            f'<text x="{cx + comp_w // 2}" y="{L3_Y + top_h - 28}" font-family="Helvetica"'
            f' font-size="11" font-weight="800" fill="{TITLE}" text-anchor="middle">{name}</text>'
            f'<text x="{cx + comp_w // 2}" y="{L3_Y + top_h - 12}" font-family="Helvetica"'
            f' font-size="8.5" fill="{DIM_LABEL}" text-anchor="middle">{role}</text>'
        )

    # Bottom row: 4 Pillar Agents
    agent_y = L3_Y + top_h + 16
    agent_h = BAND_HEIGHTS[3] - 14 - top_h - 16 - 20
    aw = (L_W - 3 * 18) // 4
    agents = [
        ("Persona Agent",     "persona",      "Claude Opus 4.7"),
        ("Creative Agent",    "creatives",    "Claude Sonnet 4.6"),
        ("Attribution Agent", "attribution",  "Claude Sonnet 4.6"),
        ("Media Agent ★",     "audience",     "Claude Sonnet 4.6"),
    ]
    for i, (n, s, model) in enumerate(agents):
        ax = L_X + i * (aw + 18)
        parts.append(tool_box(ax, agent_y, aw, agent_h, s, n, model,
                              LAYER_COLORS[3]))

    # ── LAYER 4 — ELT Transform Pipeline ──────────────────
    parts.append(layer_label(4, "ELT Transform", "5 in-warehouse stages",
                             "Orchestrator: Dagster OSS / Airflow"))
    L4_Y = band_y(4) + 28
    L4_H = BAND_HEIGHTS[4] - 56
    stages = [
        ("Normalize",   "Field standardize",   LAYER_COLORS[4]),
        ("Deduplicate", "Cross-platform dedup",LAYER_COLORS[4]),
        ("Validate",    "PHI scan + Schema",   EDGE_PII),
        ("Enrich",      "JOIN + 3rd-party",    LAYER_COLORS[4]),
        ("Index",       "Vector + MView",      LAYER_COLORS[4]),
    ]
    # Top strip: Orchestration (Dagster OSS primary + Step Functions for approvals)
    orch_h = 22
    L4_Y += orch_h + 6
    L4_H -= orch_h + 6
    dag_color = "#4F43DC"
    afw_color = "#017CEE"
    sfn_color = "#F59E0B"
    parts.append(
        f'<rect x="{L_X}" y="{L4_Y - orch_h - 6}" width="{L_W}" height="{orch_h}"'
        f' fill="{NODE_BG_2}" stroke="{dag_color}" stroke-width="1.2" rx="6"/>'
        f'<rect x="{L_X}" y="{L4_Y - orch_h - 6}" width="4" height="{orch_h}" fill="{dag_color}" rx="2"/>'
        f'<text x="{L_X + 14}" y="{L4_Y - 12}" font-family="Helvetica" font-size="10"'
        f' font-weight="800" fill="{dag_color}" letter-spacing="1.2">ORCHESTRATION · CHOOSE ONE</text>'
        f'<text x="{L_X + 200}" y="{L4_Y - 12}" font-family="Helvetica" font-size="11"'
        f' font-weight="700" fill="{TITLE}">🟪 Dagster OSS</text>'
        f'<text x="{L_X + 312}" y="{L4_Y - 12}" font-family="Helvetica" font-size="9"'
        f' fill="{DIM_LABEL}">Asset Graph · dagster-dbt · per-Agency Partition</text>'
        f'<text x="{L_X + 562}" y="{L4_Y - 12}" font-family="Helvetica" font-size="13"'
        f' font-weight="800" fill="{DIM_LABEL}">|</text>'
        f'<text x="{L_X + 578}" y="{L4_Y - 12}" font-family="Helvetica" font-size="11"'
        f' font-weight="700" fill="{afw_color}">🟦 Apache Airflow</text>'
        f'<text x="{L_X + 700}" y="{L4_Y - 12}" font-family="Helvetica" font-size="9"'
        f' fill="{DIM_LABEL}">1000+ Providers · team familiar · DAG model</text>'
        f'<text x="{L_X + L_W - 300}" y="{L4_Y - 12}" font-family="Helvetica" font-size="10"'
        f' font-weight="700" fill="{sfn_color}">🟧 AWS Step Functions</text>'
        f'<text x="{L_X + L_W - 165}" y="{L4_Y - 12}" font-family="Helvetica" font-size="9"'
        f' fill="{DIM_LABEL}">Approval · DSAR long flow</text>'
    )

    sw = (L_W - 4 * 14) // 5
    for i, (name, hint, color) in enumerate(stages):
        sx = L_X + i * (sw + 14)
        points = (f"{sx},{L4_Y} {sx+sw-16},{L4_Y} {sx+sw},{L4_Y+L4_H//2} "
                  f"{sx+sw-16},{L4_Y+L4_H} {sx},{L4_Y+L4_H} {sx+16},{L4_Y+L4_H//2}")
        parts.append(
            f'<polygon points="{points}" fill="{NODE_BG}" stroke="{color}"'
            f' stroke-width="1.6"/>'
            f'<rect x="{sx+16}" y="{L4_Y}" width="{sw-32}" height="3"'
            f' fill="{color}" rx="1.5"/>'
            f'<text x="{sx + sw//2}" y="{L4_Y + 20}" font-family="Helvetica"'
            f' font-size="10" font-weight="700" fill="{color}" text-anchor="middle">'
            f'STEP {i+1}</text>'
            f'<text x="{sx + sw//2}" y="{L4_Y + 42}" font-family="Helvetica"'
            f' font-size="15" font-weight="800" fill="{TITLE}" text-anchor="middle">'
            f'{name}</text>'
            f'<text x="{sx + sw//2}" y="{L4_Y + 60}" font-family="Helvetica"'
            f' font-size="9" fill="{DIM_LABEL}" text-anchor="middle">{hint}</text>'
        )

    # ── LAYER 5 — Two-Lake Warehouse ──────────────────────
    parts.append(layer_label(5, "3-Lake Warehouse", "on Neon",
                             "Landing → 🔴 Raw PII → 🟢 Processed"))
    L5_Y = band_y(5) + 16
    L5_H = 190
    # 3 Lakes side-by-side: ⬛ Landing | 🔴 Raw PII | (PII Boundary) | 🟢 Processed
    BRONZE = "#A16207"
    inter_gap = 14            # Landing ↔ Raw PII: same trust boundary, soft divider
    pii_boundary_gap = 30     # Raw PII ↔ Processed: PII Boundary hard divider
    lake_w = (L_W - inter_gap - pii_boundary_gap - 26) // 3

    landing_x = L_X
    raw_x = landing_x + lake_w + inter_gap
    pii_x = raw_x + lake_w + (pii_boundary_gap // 2)
    proc_x = pii_x + (pii_boundary_gap // 2)

    # ── ⬛ Landing Lake (Bronze) ─────────────────────────────
    parts.append(
        f'<rect x="{landing_x}" y="{L5_Y}" width="{lake_w}" height="{L5_H}"'
        f' fill="{BRONZE}" fill-opacity="0.08" stroke="{BRONZE}"'
        f' stroke-width="2" rx="12"/>'
        f'<rect x="{landing_x}" y="{L5_Y}" width="{lake_w}" height="5"'
        f' fill="{BRONZE}" rx="2.5"/>'
        f'<text x="{landing_x + lake_w // 2 + 12}" y="{L5_Y + 28}" font-family="Helvetica"'
        f' font-size="15" font-weight="800" fill="{BRONZE}" text-anchor="middle">'
        f'Landing Lake (Bronze)</text>'
        f'<text x="{landing_x + lake_w // 2}" y="{L5_Y + 46}" font-family="Helvetica"'
        f' font-size="10" fill="{LABEL}" text-anchor="middle">'
        f'Full record · immutable · ELT + auditors only</text>'
    )
    _lcx = landing_x + lake_w // 2
    _lbx = _lcx - 92
    _lby = L5_Y + 21
    parts.append(
        f'<rect x="{_lbx - 6}" y="{_lby}" width="12" height="9" fill="{BRONZE}" rx="1"/>'
        f'<rect x="{_lbx - 6}" y="{_lby + 4}" width="12" height="1.2" fill="{BG}"/>'
        f'<rect x="{_lbx - 0.5}" y="{_lby}" width="1.2" height="4" fill="{BG}"/>'
        f'<rect x="{_lbx - 0.5}" y="{_lby + 5.2}" width="1.2" height="4" fill="{BG}"/>'
    )
    landing_tables = [
        ("📦 &lt;source&gt;_records", "Full record · PII encrypted"),
        ("🔖 sync_state",          "cursor / watermark"),
    ]
    lcw = (lake_w - 30) // 2
    lch = 80
    lcx0 = landing_x + 10
    lcy0 = L5_Y + 62
    for i, (label, sub) in enumerate(landing_tables):
        lrx = lcx0 + i * (lcw + 10)
        parts.append(
            f'<rect x="{lrx}" y="{lcy0}" width="{lcw}" height="{lch}"'
            f' fill="{NODE_BG_2}" stroke="{BRONZE}" stroke-width="1.4" rx="9"/>'
            f'<rect x="{lrx}" y="{lcy0}" width="{lcw}" height="4"'
            f' fill="{BRONZE}" rx="2"/>'
            f'<text x="{lrx + lcw // 2}" y="{lcy0 + 30}" font-family="Menlo,Helvetica"'
            f' font-size="12" font-weight="800" fill="{BRONZE}" text-anchor="middle">{label}</text>'
            f'<text x="{lrx + lcw // 2}" y="{lcy0 + 52}" font-family="Helvetica"'
            f' font-size="9" fill="{DIM_LABEL}" text-anchor="middle">{sub}</text>'
        )
    parts.append(
        f'<text x="{landing_x + lake_w // 2}" y="{lcy0 + lch + 18}" font-family="Helvetica"'
        f' font-size="10" font-weight="700" fill="{BRONZE}" text-anchor="middle"'
        f' letter-spacing="0.6">⚠ All raw data preserved here · business/AI forbidden</text>'
    )

    # ── 🔴 Raw PII Lake ─────────────────────────────────────
    parts.append(
        f'<rect x="{raw_x}" y="{L5_Y}" width="{lake_w}" height="{L5_H}"'
        f' fill="{EDGE_PII}" fill-opacity="0.08" stroke="{EDGE_PII}"'
        f' stroke-width="2" rx="12"/>'
        f'<rect x="{raw_x}" y="{L5_Y}" width="{lake_w}" height="5"'
        f' fill="{EDGE_PII}" rx="2.5"/>'
        f'<text x="{raw_x + lake_w // 2 + 9}" y="{L5_Y + 28}" font-family="Helvetica"'
        f' font-size="15" font-weight="800" fill="{EDGE_PII}" text-anchor="middle">'
        f'Raw PII-Segregated Lake</text>'
        f'<text x="{raw_x + lake_w // 2}" y="{L5_Y + 46}" font-family="Helvetica"'
        f' font-size="10" fill="{LABEL}" text-anchor="middle">'
        f'PII fields only · per-tenant KMS · PII Access Service</text>'
    )
    _cx5 = raw_x + lake_w // 2
    _lx5 = _cx5 - 102
    _ly5 = L5_Y + 21
    parts.append(
        f'<rect x="{_lx5 - 6}" y="{_ly5}" width="12" height="11" fill="{EDGE_PII}" rx="2"/>'
        f'<path d="M {_lx5 - 3.5} {_ly5 + 1} L {_lx5 - 3.5} {_ly5 - 4} A 3.5 3.5 0 0 1 {_lx5 + 3.5} {_ly5 - 4} L {_lx5 + 3.5} {_ly5 + 1}"'
        f' stroke="{EDGE_PII}" stroke-width="1.8" fill="none"/>'
    )
    raw_tables = [
        ("👤 users",          "subject dim"),
        ("📇 *_pii_fields",   "per-source PII cols"),
        ("📝 pii_access_log", "egress audit"),
    ]
    rcw = (lake_w - 22) // 3
    rch = 80
    rcx0 = raw_x + 6
    rcy0 = L5_Y + 62
    for i, (label, sub) in enumerate(raw_tables):
        rrx = rcx0 + i * (rcw + 5)
        parts.append(
            f'<rect x="{rrx}" y="{rcy0}" width="{rcw}" height="{rch}"'
            f' fill="{NODE_BG_2}" stroke="{EDGE_PII}" stroke-width="1.4" rx="9"/>'
            f'<rect x="{rrx}" y="{rcy0}" width="{rcw}" height="4"'
            f' fill="{EDGE_PII}" rx="2"/>'
            f'<text x="{rrx + rcw // 2}" y="{rcy0 + 30}" font-family="Menlo,Helvetica"'
            f' font-size="11" font-weight="800" fill="{EDGE_PII}" text-anchor="middle">{label}</text>'
            f'<text x="{rrx + rcw // 2}" y="{rcy0 + 52}" font-family="Helvetica"'
            f' font-size="8.5" fill="{DIM_LABEL}" text-anchor="middle">{sub}</text>'
        )
    parts.append(
        f'<text x="{raw_x + lake_w // 2}" y="{rcy0 + rch + 18}" font-family="Helvetica"'
        f' font-size="10" font-weight="700" fill="{EDGE_PII}" text-anchor="middle"'
        f' letter-spacing="0.6">⚠ PII fields ONLY · non-PII never here</text>'
    )

    # ── PII Boundary (between Raw PII and Processed only) ───
    parts.append(
        f'<line x1="{pii_x}" y1="{L5_Y - 4}" x2="{pii_x}" y2="{L5_Y + L5_H + 4}"'
        f' stroke="{EDGE_PII}" stroke-width="3.5" stroke-dasharray="14 6"/>'
        f'<rect x="{pii_x - 26}" y="{L5_Y + L5_H // 2 - 32}" width="52" height="64"'
        f' fill="{BG}" stroke="{EDGE_PII}" stroke-width="2.4" rx="10"/>'
        f'<text x="{pii_x}" y="{L5_Y + L5_H // 2 - 6}" font-family="Helvetica"'
        f' font-size="24" text-anchor="middle">🔐</text>'
        f'<text x="{pii_x}" y="{L5_Y + L5_H // 2 + 14}" font-family="Helvetica"'
        f' font-size="8" font-weight="800" fill="{EDGE_PII}" text-anchor="middle">PII</text>'
        f'<text x="{pii_x}" y="{L5_Y + L5_H // 2 + 24}" font-family="Helvetica"'
        f' font-size="8" font-weight="800" fill="{EDGE_PII}" text-anchor="middle">BOUNDARY</text>'
    )

    # ⬛ ↔ 🔴 soft divider (same trust boundary, no PII Boundary)
    inter_x = (raw_x - inter_gap // 2)
    parts.append(
        f'<line x1="{inter_x}" y1="{L5_Y + 12}" x2="{inter_x}" y2="{L5_Y + L5_H - 12}"'
        f' stroke="{BRONZE}" stroke-width="1.4" stroke-dasharray="3 4" opacity="0.6"/>'
        f'<text x="{inter_x}" y="{L5_Y + L5_H // 2}" font-family="Helvetica"'
        f' font-size="8" fill="{DIM_LABEL}" text-anchor="middle" opacity="0.8">same PII zone</text>'
    )

    # Processed Lake
    parts.append(
        f'<rect x="{proc_x}" y="{L5_Y}" width="{lake_w}" height="{L5_H}"'
        f' fill="{LAYER_COLORS[5]}" fill-opacity="0.10" stroke="{LAYER_COLORS[5]}"'
        f' stroke-width="2" rx="12"/>'
        f'<rect x="{proc_x}" y="{L5_Y}" width="{lake_w}" height="5"'
        f' fill="{LAYER_COLORS[5]}" rx="2.5"/>'
        f'<text x="{proc_x + lake_w // 2}" y="{L5_Y + 28}" font-family="Helvetica"'
        f' font-size="16" font-weight="800" fill="{LAYER_COLORS[5]}" text-anchor="middle">'
        f'✓ Processed Lake</text>'
        f'<text x="{proc_x + lake_w // 2}" y="{L5_Y + 46}" font-family="Helvetica"'
        f' font-size="10" fill="{LABEL}" text-anchor="middle">'
        f'Per-tenant DB · Canonical · Branch Clone · business-ready</text>'
    )
    # Processed Lake holds non-PII data + dbt 4 layers
    proc_tables = [
        ("📥 raw.*",      "non-PII raw",  "STAGE 1"),
        ("📦 staging",    "dbt staging",  "STAGE 4.1"),
        ("🧱 canonical",  "13 entities",  "STAGE 4.2"),
        ("📊 marts",      "reports",      "STAGE 4.3"),
        ("🧠 ai_context", "AI retrieval", "STAGE 4.4"),
    ]
    cw_p = (lake_w - 8 * 6) // 5
    ch_p = 64
    pgap = 6
    cy0 = L5_Y + 62  # shared baseline with Landing / Raw PII inner tables
    cx02 = proc_x + (lake_w - (len(proc_tables) * cw_p + (len(proc_tables) - 1) * pgap)) // 2
    for i, (label, sub, stage_tag) in enumerate(proc_tables):
        rx = cx02 + i * (cw_p + pgap)
        parts.append(
            f'<rect x="{rx}" y="{cy0}" width="{cw_p}" height="{ch_p}"'
            f' fill="{NODE_BG_2}" stroke="{LAYER_COLORS[5]}" stroke-width="1.4" rx="9"/>'
            f'<rect x="{rx}" y="{cy0}" width="{cw_p}" height="4"'
            f' fill="{LAYER_COLORS[5]}" rx="2"/>'
            f'<text x="{rx + cw_p // 2}" y="{cy0 + 13}" font-family="Helvetica"'
            f' font-size="8.5" font-weight="800" fill="{LAYER_COLORS[5]}" text-anchor="middle"'
            f' letter-spacing="0.8">{stage_tag}</text>'
            f'<text x="{rx + cw_p // 2}" y="{cy0 + 34}" font-family="Menlo,Helvetica"'
            f' font-size="11.5" font-weight="800" fill="{LAYER_COLORS[5]}" text-anchor="middle">{label}</text>'
            f'<text x="{rx + cw_p // 2}" y="{cy0 + 52}" font-family="Helvetica"'
            f' font-size="9" fill="{DIM_LABEL}" text-anchor="middle">{sub}</text>'
        )
        if i < len(proc_tables) - 1:
            ax = rx + cw_p + 1
            ay = cy0 + ch_p // 2
            parts.append(
                f'<path d="M {ax} {ay - 4} L {ax + 4} {ay} L {ax} {ay + 4}"'
                f' stroke="{LAYER_COLORS[5]}" stroke-width="2"'
                f' stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
            )
    parts.append(
        f'<text x="{proc_x + lake_w // 2}" y="{cy0 + ch_p + 18}" font-family="Helvetica"'
        f' font-size="10" font-weight="700" fill="{LAYER_COLORS[5]}" text-anchor="middle"'
        f' letter-spacing="0.8">✓ No plaintext PII anywhere · pii_token (irreversible hash) only</text>'
    )

    # Neon icon (warehouse choice)
    sf_icon = img_b64("neon")
    if sf_icon:
        parts.append(
            f'<image href="{sf_icon}" x="{CR - 56}" y="{L5_Y + 4}"'
            f' width="36" height="36"/>'
            f'<text x="{CR - 38}" y="{L5_Y + 52}" font-family="Helvetica" font-size="9"'
            f' fill="{DIM_LABEL}" text-anchor="middle">Neon Postgres</text>'
        )

    # ────────────────────────────────────────────────────────────
    # Data Lifecycle Ribbon (lower half of L5 band)
    # Layout top→bottom:
    #   y+0:   title bar
    #   y+24:  title (line 1)
    #   y+44:  subtitle (line 2)
    #   y+60:  4 STAGE cards (h=168)
    #   y+240: DEDUP strip (h=36)
    # Total lifecycle_h = 276
    # ────────────────────────────────────────────────────────────
    lifecycle_y0 = L5_Y + L5_H + 10
    lifecycle_h = 276
    parts.append(
        f'<rect x="{L_X}" y="{lifecycle_y0}" width="{L_W}" height="{lifecycle_h}"'
        f' fill="{NODE_BG_2}" stroke="{EDGE_GUARD}" stroke-opacity="0.55"'
        f' stroke-width="1.6" rx="14" stroke-dasharray="6 4"/>'
        f'<rect x="{L_X}" y="{lifecycle_y0}" width="{L_W}" height="5"'
        f' fill="{EDGE_GUARD}" rx="2.5"/>'
    )
    parts.append(
        f'<text x="{L_X + 16}" y="{lifecycle_y0 + 24}" font-family="Helvetica"'
        f' font-size="15" font-weight="800" fill="{EDGE_GUARD}" letter-spacing="1.5">'
        f'▸ DATA LIFECYCLE</text>'
    )
    parts.append(
        f'<text x="{L_X + 16}" y="{lifecycle_y0 + 44}" font-family="Helvetica"'
        f' font-size="11" fill="{DIM_LABEL}">'
        f'Raw data → business warehouse, end-to-end (linked to the Two-Lake above)</text>'
    )
    # Top-right: Lake ownership legend (4-Lake architecture)
    legend_x = L_X + L_W - 640
    parts.append(
        f'<rect x="{legend_x - 8}" y="{lifecycle_y0 + 28}" width="638" height="22"'
        f' fill="{NODE_BG}" stroke="#1F2937" stroke-width="1" rx="6"/>'
        f'<circle cx="{legend_x + 4}" cy="{lifecycle_y0 + 39}" r="5" fill="#A16207"/>'
        f'<text x="{legend_x + 14}" y="{lifecycle_y0 + 42}" font-family="Helvetica"'
        f' font-size="9.5" font-weight="700" fill="#A16207">Landing (Bronze)</text>'
        f'<circle cx="{legend_x + 150}" cy="{lifecycle_y0 + 39}" r="5" fill="{EDGE_PII}"/>'
        f'<text x="{legend_x + 160}" y="{lifecycle_y0 + 42}" font-family="Helvetica"'
        f' font-size="9.5" font-weight="700" fill="{EDGE_PII}">🔴 Raw PII Lake</text>'
        f'<circle cx="{legend_x + 290}" cy="{lifecycle_y0 + 39}" r="5" fill="{LAYER_COLORS[5]}"/>'
        f'<text x="{legend_x + 300}" y="{lifecycle_y0 + 42}" font-family="Helvetica"'
        f' font-size="9.5" font-weight="700" fill="{LAYER_COLORS[5]}">🟢 Processed Lake</text>'
        f'<text x="{legend_x + 430}" y="{lifecycle_y0 + 42}" font-family="Helvetica"'
        f' font-size="9.5" font-weight="700" fill="{EDGE_GUARD}">🚦 Process only</text>'
        f'<text x="{legend_x + 510}" y="{lifecycle_y0 + 42}" font-family="Helvetica"'
        f' font-size="9" fill="{DIM_LABEL}">(in-mem · no Lake write)</text>'
    )
    raw_lake_center_x = L_X + lake_w // 2
    proc_lake_center_x = proc_x + lake_w // 2
    parts.append(
        f'<line x1="{raw_lake_center_x}" y1="{L5_Y + L5_H}" x2="{raw_lake_center_x}" y2="{lifecycle_y0 + 4}"'
        f' stroke="{EDGE_PII}" stroke-width="2" stroke-dasharray="4 4"/>'
        f'<line x1="{proc_lake_center_x}" y1="{L5_Y + L5_H}" x2="{proc_lake_center_x}" y2="{lifecycle_y0 + 4}"'
        f' stroke="{LAYER_COLORS[5]}" stroke-width="2" stroke-dasharray="4 4"/>'
    )

    stage_y = lifecycle_y0 + 60
    stage_h = 168
    stage1_w = 230
    arrow_w = 28
    margin_left = 16
    used_w = stage1_w * 3 + arrow_w * 3 + margin_left * 2
    stage4_w = L_W - used_w
    cur_sx = L_X + margin_left

    # Each STAGE card marks its output Lake (⬛ Landing / 🔴 PII / 🟢 Processed / 🚦 process-only)
    stage_defs = [
        ("STAGE 1", "LAND", "Full record → Bronze",
         [("landing.&lt;source&gt;_records", "Full record · PII cols encrypted"),
          ("landing.sync_state",         "cursor / watermark state")],
         "Writes Landing Lake · immutable · HIPAA 6y / non-HIPAA 90d",
         "#A16207"),
        ("STAGE 2", "CLASSIFY", "Read Landing, tag per-field",
         [("PHI Detector",   "HIPAA 18-id scan"),
          ("PII Classifier", "L0 / L1 / L2 / L3 tagging")],
         "🚦 Process only · outputs field_classification_manifest",
         LAYER_COLORS[4]),
        ("STAGE 3", "SPLIT", "Read Landing, derive to both",
         [("🔴 PII fields → 🔴 Raw PII Lake",    "raw_secure.users + *_pii_fields"),
          ("🟢 non-PII fields → 🟢 Processed Lake", "processed.raw.&lt;source&gt;_records")],
         "pii_token = SHA-256(email_hash + agency_salt) links both sides",
         "#F59E0B"),
    ]
    for i, (st_num, st_name, st_desc, items, footer, st_color) in enumerate(stage_defs):
        parts.append(
            f'<rect x="{cur_sx}" y="{stage_y}" width="{stage1_w}" height="{stage_h}"'
            f' fill="{NODE_BG}" stroke="{st_color}" stroke-width="2" rx="10"/>'
            f'<rect x="{cur_sx}" y="{stage_y}" width="{stage1_w}" height="4"'
            f' fill="{st_color}" rx="2"/>'
            f'<text x="{cur_sx + 12}" y="{stage_y + 22}" font-family="Helvetica"'
            f' font-size="10" font-weight="800" fill="{st_color}" letter-spacing="1.4">{st_num}</text>'
            f'<text x="{cur_sx + 12}" y="{stage_y + 42}" font-family="Helvetica"'
            f' font-size="18" font-weight="800" fill="{TITLE}">{st_name}</text>'
            f'<text x="{cur_sx + 12}" y="{stage_y + 60}" font-family="Helvetica"'
            f' font-size="10" fill="{DIM_LABEL}">{st_desc}</text>'
        )
        item_y = stage_y + 78
        for j, (title, sub) in enumerate(items):
            iy = item_y + j * 30
            parts.append(
                f'<rect x="{cur_sx + 10}" y="{iy}" width="{stage1_w - 20}" height="26"'
                f' fill="{NODE_BG_2}" stroke="{st_color}" stroke-opacity="0.4"'
                f' stroke-width="1" rx="5"/>'
                f'<text x="{cur_sx + 18}" y="{iy + 12}" font-family="Menlo,Helvetica"'
                f' font-size="9.5" font-weight="800" fill="{st_color}">{title}</text>'
                f'<text x="{cur_sx + 18}" y="{iy + 22}" font-family="Helvetica"'
                f' font-size="8.5" fill="{DIM_LABEL}">{sub}</text>'
            )
        parts.append(
            f'<text x="{cur_sx + 12}" y="{stage_y + stage_h - 8}" font-family="Helvetica"'
            f' font-size="8.5" font-style="italic" fill="{DIM_LABEL}">{footer}</text>'
        )
        ax_start = cur_sx + stage1_w + 3
        ay_mid = stage_y + stage_h // 2
        next_color = stage_defs[i + 1][5] if i + 1 < len(stage_defs) else LAYER_COLORS[5]
        parts.append(
            f'<path d="M {ax_start} {ay_mid} L {ax_start + arrow_w - 8} {ay_mid}"'
            f' stroke="{next_color}" stroke-width="3"/>'
            f'<path d="M {ax_start + arrow_w - 14} {ay_mid - 7} L {ax_start + arrow_w - 4} {ay_mid} L {ax_start + arrow_w - 14} {ay_mid + 7}"'
            f' fill="{next_color}"/>'
        )
        cur_sx += stage1_w + arrow_w

    s4_x = cur_sx
    s4_color = LAYER_COLORS[5]
    parts.append(
        f'<rect x="{s4_x}" y="{stage_y}" width="{stage4_w}" height="{stage_h}"'
        f' fill="{NODE_BG}" stroke="{s4_color}" stroke-width="2.4" rx="10"/>'
        f'<rect x="{s4_x}" y="{stage_y}" width="{stage4_w}" height="4"'
        f' fill="{s4_color}" rx="2"/>'
        f'<text x="{s4_x + 12}" y="{stage_y + 22}" font-family="Helvetica"'
        f' font-size="10" font-weight="800" fill="{s4_color}" letter-spacing="1.4">STAGE 4</text>'
        f'<text x="{s4_x + 12}" y="{stage_y + 42}" font-family="Helvetica"'
        f' font-size="18" font-weight="800" fill="{TITLE}">TRANSFORM</text>'
        f'<text x="{s4_x + 12}" y="{stage_y + 60}" font-family="Helvetica"'
        f' font-size="10" fill="{DIM_LABEL}">dbt 4 layers · inside Processed Lake</text>'
    )
    sub_y = stage_y + 76
    sub_h = 50
    sub_layers = [
        ("📥 raw.*",      "non-PII raw",      "#10B981"),
        ("📦 staging",    "30d staging",      "#22D3EE"),
        ("🧱 canonical",  "13 entities·3y",  LAYER_COLORS[5]),
        ("📊 marts",      "reports·3-7y",    "#A78BFA"),
        ("🧠 ai_context", "vectors·1y",      LAYER_COLORS[3]),
    ]
    sub_pad = 14
    sub_arrow = 18
    sub_block_w = stage4_w - sub_pad * 2 - sub_arrow * (len(sub_layers) - 1)
    sub_w = sub_block_w // len(sub_layers)
    sx_cur = s4_x + sub_pad
    for j, (sub_name, sub_desc, sub_color) in enumerate(sub_layers):
        parts.append(
            f'<rect x="{sx_cur}" y="{sub_y}" width="{sub_w}" height="{sub_h}"'
            f' fill="{NODE_BG_2}" stroke="{sub_color}" stroke-width="1.4" rx="7"/>'
            f'<rect x="{sx_cur}" y="{sub_y}" width="{sub_w}" height="3"'
            f' fill="{sub_color}" rx="1.5"/>'
            f'<text x="{sx_cur + sub_w // 2}" y="{sub_y + 22}" font-family="Helvetica"'
            f' font-size="11.5" font-weight="800" fill="{sub_color}" text-anchor="middle">{sub_name}</text>'
            f'<text x="{sx_cur + sub_w // 2}" y="{sub_y + 40}" font-family="Helvetica"'
            f' font-size="9" fill="{DIM_LABEL}" text-anchor="middle">{sub_desc}</text>'
        )
        if j < len(sub_layers) - 1:
            ax = sx_cur + sub_w + 2
            ay = sub_y + sub_h // 2
            next_sub_color = sub_layers[j + 1][2]
            parts.append(
                f'<path d="M {ax} {ay} L {ax + sub_arrow - 6} {ay}"'
                f' stroke="{next_sub_color}" stroke-width="2.4"/>'
                f'<path d="M {ax + sub_arrow - 10} {ay - 4} L {ax + sub_arrow - 4} {ay} L {ax + sub_arrow - 10} {ay + 4}"'
                f' fill="{next_sub_color}"/>'
            )
        sx_cur += sub_w + sub_arrow

    parts.append(
        f'<text x="{s4_x + 12}" y="{stage_y + stage_h - 8}" font-family="Helvetica"'
        f' font-size="8.5" font-style="italic" fill="{DIM_LABEL}">'
        f'audit schema cross-cuts · INSERT-only 6y · DSAR / reprocessing / audit replayable via dbt lineage</text>'
    )

    parts.append(
        f'<text x="{raw_lake_center_x}" y="{lifecycle_y0 - 4}" font-family="Helvetica"'
        f' font-size="9" font-weight="700" fill="{EDGE_PII}" text-anchor="middle">'
        f'PII columns encrypted ↓</text>'
        f'<text x="{proc_lake_center_x}" y="{lifecycle_y0 - 4}" font-family="Helvetica"'
        f' font-size="9" font-weight="700" fill="{LAYER_COLORS[5]}" text-anchor="middle">'
        f'non-PII + pii_token ↓</text>'
    )

    # ────────────────────────────────────────────────────────────
    # DEDUP strip: how duplicate data is handled (5 mechanisms in parallel)
    # ────────────────────────────────────────────────────────────
    dedup_y = stage_y + stage_h + 12
    dedup_h = 36
    dedup_color = "#22D3EE"  # cyan
    parts.append(
        f'<rect x="{L_X + 8}" y="{dedup_y}" width="{L_W - 16}" height="{dedup_h}"'
        f' fill="{NODE_BG}" stroke="{dedup_color}" stroke-width="1.4" rx="9"/>'
        f'<rect x="{L_X + 8}" y="{dedup_y}" width="6" height="{dedup_h}"'
        f' fill="{dedup_color}" rx="3"/>'
        f'<text x="{L_X + 26}" y="{dedup_y + 14}" font-family="Helvetica"'
        f' font-size="10" font-weight="800" fill="{dedup_color}" letter-spacing="1.3">'
        f'▸ DEDUP (spans all 4 STAGES)</text>'
        f'<text x="{L_X + 26}" y="{dedup_y + 28}" font-family="Helvetica"'
        f' font-size="9" fill="{DIM_LABEL}">'
        f'A record is never written twice; 5 mechanisms in parallel</text>'
    )
    dedup_items = [
        ("① Cursor resume",      "stored last pos · only pull new rows"),
        ("② Content hash",       "UNIQUE SHA-256(record)"),
        ("③ MERGE upsert",       "merge by biz key · not INSERT"),
        ("④ Fixed cadence",      "B: cycle / A: 5min guard"),
        ("⑤ Audit fingerprint",  "per-batch new/skipped count"),
    ]
    chip_area_x = L_X + 280
    chip_area_w = L_W - 16 - (chip_area_x - L_X) - 10
    chip_w = (chip_area_w - 4 * 6) // 5
    for i, (name, sub) in enumerate(dedup_items):
        cx = chip_area_x + i * (chip_w + 6)
        parts.append(
            f'<rect x="{cx}" y="{dedup_y + 5}" width="{chip_w}" height="{dedup_h - 10}"'
            f' fill="{NODE_BG_2}" stroke="{dedup_color}" stroke-opacity="0.5"'
            f' stroke-width="1" rx="6"/>'
            f'<text x="{cx + 8}" y="{dedup_y + 16}" font-family="Helvetica"'
            f' font-size="10" font-weight="800" fill="{dedup_color}">{name}</text>'
            f'<text x="{cx + 8}" y="{dedup_y + 28}" font-family="Helvetica"'
            f' font-size="8.5" fill="{DIM_LABEL}">{sub}</text>'
        )

    # ── LAYER 6 — External Sources ────────────────────────
    parts.append(layer_label(6, "External Sources", "Priority-1 Integrations",
                             "14 sources"))
    L6_Y = band_y(6) + 14
    cats = [
        ("Audience / CRM", ["experian", "transunion", "liveramp", "hubspot", "plus_more"]),
        ("Measurement",    ["nielsen", "placeriq"]),
        ("Ad Platforms",   ["dv360", "meta", "tiktok", "trade_desk", "stackadapt", "plus_more"]),
        ("Analytics",      ["ga4"]),
        ("Advocacy",       ["quorum"]),
        ("Compliant CRM",  ["tresorit"]),
    ]
    # Name label
    disp = {
        "experian": "Experian", "transunion": "TransUnion", "liveramp": "LiveRamp",
        "nielsen": "Nielsen", "placeriq": "Placer IQ",
        "dv360": "DV360", "meta": "Meta", "tiktok": "TikTok",
        "trade_desk": "Trade Desk", "ga4": "GA4", "quorum": "Quorum",
        "tresorit": "Tresorit", "stackadapt": "StackAdapt", "plus_more": "+More",
    }
    # Category title row
    cat_y = L6_Y + 6
    chip_y = L6_Y + 38
    cw3, gap3 = 88, 8  # shrunk to avoid right-boundary overflow (L_W=1670)
    inter_cat_gap = 16
    cat_widths = [len(s) * cw3 + (len(s) - 1) * gap3 for _, s in cats]
    total_used = sum(cat_widths) + (len(cats) - 1) * inter_cat_gap
    margin = max(0, (L_W - total_used) // 2)
    cur_x = L_X + margin
    for (cat_name, slugs), cw_total in zip(cats, cat_widths):
        # Title
        parts.append(
            f'<rect x="{cur_x}" y="{cat_y}" width="{cw_total}" height="22"'
            f' fill="{LAYER_COLORS[6]}" fill-opacity="0.14" stroke="{LAYER_COLORS[6]}"'
            f' stroke-opacity="0.5" stroke-width="1" rx="5"/>'
            f'<text x="{cur_x + cw_total // 2}" y="{cat_y + 16}" font-family="Helvetica"'
            f' font-size="10" font-weight="700" fill="{LAYER_COLORS[6]}"'
            f' text-anchor="middle" letter-spacing="1">{cat_name}</text>'
        )
        for i, slug in enumerate(slugs):
            cx = cur_x + i * (cw3 + gap3)
            parts.append(small_chip(cx, chip_y, slug, disp.get(slug, slug.title()),
                                    w=cw3, h=88, accent=LAYER_COLORS[6]))
        cur_x += cw_total + inter_cat_gap

    # ── LAYER 7 — Infrastructure · Cross-Cutting ──────────
    parts.append(layer_label(7, "Infrastructure", "Cross-Cutting",
                             "Compute · Observability · Secrets"))
    L7_Y = band_y(7) + 22
    L7_H = BAND_HEIGHTS[7] - 44
    infra_items = [
        ("Render PaaS",   "render",   "Prod compute (multi-region)"),
        ("Coolify",       "coolify",  "Dev compute (self-host)"),
        ("Langfuse",      "langfuse", "LLM tracing"),
        ("Sentry",        "sentry",   "Error monitoring"),
        ("AWS S3",        "aws_s3",   "Object storage · PDF / CSV / files"),
        ("GitHub",        "github",   "Source + CI/CD"),
    ]
    iw = (L_W - 5 * 14) // 6
    for i, (n, s, r) in enumerate(infra_items):
        ix = L_X + i * (iw + 14)
        parts.append(tool_box(ix, L7_Y, iw, L7_H, s, n, r, LAYER_COLORS[7]))

    # ─────────────────────────────────────────────────
    # Right-side Compliance Panel (spine + top/bottom cards + horizontal anchors)
    # ─────────────────────────────────────────────────
    COMP_X = CR + 30
    COMP_W = W - COMP_X - 30
    SPINE_X = COMP_X - 16

    # Horizontal connector lines (each layer → spine)
    for layer in range(1, 8):
        ay = band_y(layer) + BAND_HEIGHTS[layer] // 2
        parts.append(
            f'<line x1="{CR - 8}" y1="{ay}" x2="{SPINE_X}" y2="{ay}"'
            f' stroke="{EDGE_GUARD}" stroke-width="1.4" stroke-dasharray="4 4"'
            f' opacity="0.55"/>'
            f'<circle cx="{SPINE_X}" cy="{ay}" r="3.5" fill="{EDGE_GUARD}"'
            f' opacity="0.85"/>'
        )

    # spine
    spine_top = band_y(1) + BAND_HEIGHTS[1] // 2 - 8
    spine_bot = band_y(7) + BAND_HEIGHTS[7] // 2 + 8
    parts.append(
        f'<line x1="{SPINE_X}" y1="{spine_top}" x2="{SPINE_X}" y2="{spine_bot}"'
        f' stroke="{EDGE_GUARD}" stroke-width="2" opacity="0.7"/>'
    )

    # Top card: four compliance principles
    TOP_Y = band_y(2) - 18
    TOP_H = 280
    parts.append(
        f'<defs><linearGradient id="grad-c-top" x1="0%" y1="0%" x2="0%" y2="100%">'
        f'<stop offset="0%" stop-color="{EDGE_GUARD}" stop-opacity="0.20"/>'
        f'<stop offset="100%" stop-color="{EDGE_GUARD}" stop-opacity="0.05"/>'
        f'</linearGradient></defs>'
        f'<rect x="{COMP_X}" y="{TOP_Y}" width="{COMP_W}" height="{TOP_H}"'
        f' fill="url(#grad-c-top)" stroke="{EDGE_GUARD}" stroke-width="2.5" rx="14"/>'
        f'<rect x="{COMP_X}" y="{TOP_Y}" width="{COMP_W}" height="6"'
        f' fill="{EDGE_GUARD}" rx="3"/>'
    )
    icon = img_b64("compliance")
    if icon:
        parts.append(
            f'<image href="{icon}" x="{COMP_X + COMP_W // 2 - 24}" y="{TOP_Y + 18}"'
            f' width="48" height="48"/>'
        )
    parts.append(
        f'<text x="{COMP_X + COMP_W // 2}" y="{TOP_Y + 88}" font-family="Helvetica"'
        f' font-size="18" font-weight="800" fill="{EDGE_GUARD}" text-anchor="middle">'
        f'COMPLIANCE</text>'
        f'<text x="{COMP_X + COMP_W // 2}" y="{TOP_Y + 106}" font-family="Helvetica"'
        f' font-size="10" font-weight="600" fill="{LABEL}" text-anchor="middle">'
        f'Mandatory · L1 → L7</text>'
    )
    regs = [
        ("GDPR",    "EU · 30d DSAR · 72h Breach"),
        ("CCPA",    "CA · 45d DSAR"),
        ("HIPAA",   "Health · 60d Breach · BAA"),
        ("SOC 2",   "Type II · 5 Trust Principles"),
        ("Residency", "Per-Tenant Region"),
    ]
    for i, (code, hint) in enumerate(regs):
        by = TOP_Y + 126 + i * 30
        parts.append(
            f'<rect x="{COMP_X + 12}" y="{by}" width="{COMP_W - 24}" height="26"'
            f' fill="{EDGE_GUARD}" fill-opacity="0.14" stroke="{EDGE_GUARD}"'
            f' stroke-opacity="0.55" stroke-width="1" rx="7"/>'
            f'<text x="{COMP_X + 22}" y="{by + 17}" font-family="Helvetica"'
            f' font-size="11" font-weight="800" fill="{EDGE_GUARD}">{code}</text>'
            f'<text x="{COMP_X + COMP_W - 22}" y="{by + 17}" font-family="Helvetica"'
            f' font-size="9" fill="{LABEL}" text-anchor="end">{hint}</text>'
        )

    # Bottom card: core capabilities
    BOT_Y = band_y(5) + 16
    BOT_H = 280
    parts.append(
        f'<defs><linearGradient id="grad-c-bot" x1="0%" y1="0%" x2="0%" y2="100%">'
        f'<stop offset="0%" stop-color="{EDGE_GUARD}" stop-opacity="0.18"/>'
        f'<stop offset="100%" stop-color="{EDGE_GUARD}" stop-opacity="0.04"/>'
        f'</linearGradient></defs>'
        f'<rect x="{COMP_X}" y="{BOT_Y}" width="{COMP_W}" height="{BOT_H}"'
        f' fill="url(#grad-c-bot)" stroke="{EDGE_GUARD}" stroke-width="2.5" rx="14"/>'
        f'<rect x="{COMP_X}" y="{BOT_Y}" width="{COMP_W}" height="6"'
        f' fill="{EDGE_GUARD}" rx="3"/>'
        f'<text x="{COMP_X + COMP_W // 2}" y="{BOT_Y + 26}" font-family="Helvetica"'
        f' font-size="11" font-weight="800" fill="{EDGE_GUARD}" text-anchor="middle"'
        f' letter-spacing="2">▸ CAPABILITIES</text>'
    )
    caps = [
        "PHI Detector · 18-id scan",
        "Anonymizer · SHA-256 + salt",
        "Agency Salt isolation",
        "IP truncate (v4/24 · v6/48)",
        "Fernet field encryption",
        "Audit Log · 6y INSERT-only",
        "DSAR (30 / 45 / 30 d)",
        "Retention engine",
        "Breach notification (72h / 60d)",
        "BAA status tracking",
        "Key rotation per-Agency",
        "Data residency DLP enforcer",
    ]
    cy = BOT_Y + 50
    for cap in caps:
        parts.append(
            f'<circle cx="{COMP_X + 18}" cy="{cy - 4}" r="2.5" fill="{EDGE_GUARD}"/>'
            f'<text x="{COMP_X + 26}" y="{cy}" font-family="Helvetica" font-size="10"'
            f' fill="{LABEL}">{cap}</text>'
        )
        cy += 17

    # ─────────────────────────────────────────────────
    # Bottom Key Constraints bar
    # ─────────────────────────────────────────────────
    kc_y = H - 100
    kc_x = PAD
    kc_w = W - PAD * 2
    parts.append(
        f'<rect x="{kc_x}" y="{kc_y}" width="{kc_w}" height="76"'
        f' fill="{NODE_BG}" stroke="#1F2937" stroke-width="1" rx="12"/>'
        f'<text x="{kc_x + 18}" y="{kc_y + 24}" font-family="Helvetica" font-size="12"'
        f' font-weight="800" fill="{TITLE}" letter-spacing="2">'
        f'▸ KEY CONSTRAINTS</text>'
    )
    constraints = [
        ("Residency",  "Per-tenant region; cross-region forbidden"),
        ("Encryption", "AES-256 at rest · TLS 1.3 in transit · per-tenant KMS"),
        ("Auth",       "MVP: JWT + Google OAuth · Post-MVP: Office 365"),
        ("LLM Routing","OpenRouter default · HIPAA → Bedrock BAA"),
        ("Audit",      "INSERT-only · HIPAA 6y · Financial 7y"),
        ("Multi-Tenant","Physical: per-tenant DB + KMS; RLS as defense-in-depth"),
    ]
    col_w = (kc_w - 36) // 3
    for i, (k, v) in enumerate(constraints):
        col = i % 3
        row = i // 3
        cx = kc_x + 18 + col * col_w
        cy = kc_y + 44 + row * 16
        parts.append(
            f'<text x="{cx}" y="{cy}" font-family="Helvetica" font-size="10"'
            f' font-weight="700" fill="{EDGE_GUARD}">{k}:</text>'
            f'<text x="{cx + 90}" y="{cy}" font-family="Helvetica" font-size="10"'
            f' fill="{LABEL}">{v}</text>'
        )

    # Inter-band flow strips (6 · turns "stacked components" into end-to-end relations)
    # Note: this is a layered view, not a strict top-to-bottom flow.
    #   L1→L4 = user/AI request direction (down); L4→L5 = ELT writes warehouse;
    #   L6 → L4 = ingestion (up). Strip text labels each relationship.
    parts.append(flow_strip(
        1, 2, "① User → Pillar",
        "Agency / Client users invoke the 5 business pillars in portal",
        LAYER_COLORS[2]))
    parts.append(flow_strip(
        2, 3, "② Pillar → Core AI Brain",
        "5 pillars call the unified orchestration layer (6 components + 4 agents)",
        LAYER_COLORS[3]))
    parts.append(flow_strip(
        3, 4, "③ AI triggers ELT / reads data",
        "Agents call Tool Executor → ELT incremental runs + warehouse reads",
        LAYER_COLORS[4]))
    parts.append(flow_strip(
        4, 5, "④ ELT writes warehouse",
        "Normalize → Dedup → Validate → Enrich → Index → marts / ai_context",
        LAYER_COLORS[5]))
    parts.append(flow_strip(
        5, 6, "⑤ Warehouse ⇡ Ingestion from sources",
        "ELT pulls 14 P1 external sources (direction is L6 → L5)",
        LAYER_COLORS[6], direction="up"))
    parts.append(flow_strip(
        6, 7, "⑥ Whole stack runs on infrastructure",
        "Compute · Observability · Secrets · CI/CD cross-cuts L1-L6",
        LAYER_COLORS[7]))

    parts.append('</svg>')
    return "\n".join(parts)


def main() -> None:
    svg = build_svg()
    OUT_DIR.mkdir(exist_ok=True, parents=True)
    out_svg = OUT_DIR / "architecture-schema-en.svg"
    out_svg.write_text(svg)
    print(f"✓ wrote {out_svg} ({len(svg):,} bytes)")
    out_png = OUT_DIR / "architecture-schema-en.png"
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
