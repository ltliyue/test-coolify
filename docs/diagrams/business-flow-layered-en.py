#!/usr/bin/env python3
"""ReceptivIQ Platform — Business Flow Map (full sub-feature edition)

Six-layer customer journey; each module is annotated with:
  · Role · User · Input · Output · API · Tech stack
  · Complete sub-feature list
"""
from __future__ import annotations
import base64
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
ICONS = ROOT / "icons"

BG          = "#0B1220"
NODE_BG     = "#111B2D"
NODE_BG_2   = "#0F1729"
TITLE       = "#F8FAFC"
LABEL       = "#E2E8F0"
DIM_LABEL   = "#94A3B8"
MUTED       = "#64748B"
EDGE_DATA   = "#22D3EE"
EDGE_USER   = "#A78BFA"
EDGE_AI     = "#F472B6"
EDGE_GUARD  = "#F59E0B"

LAYER_COLORS = {
    1: "#06B6D4", 2: "#3B82F6", 3: "#EC4899",
    4: "#10B981", 5: "#8B5CF6", 6: "#F59E0B",
}

W, H = 2200, 3060
PAD = 40
LAYER_LABEL_W = 220

BAND_TOP = 170
BAND_GAP = 60
BAND_HEIGHTS = {1: 400, 2: 400, 3: 400, 4: 400, 5: 400, 6: 400}

CARD_MAX_W_BY_N = {2: 720, 3: 560, 4: 450}
CARD_GAP = 40


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


def text_w(s: str, font_px: int = 11) -> int:
    cn = sum(1 for ch in s if ord(ch) > 127)
    en = len(s) - cn
    return int(cn * font_px + en * font_px * 0.6)


# ── Layer labels on left (auto-wrap) ───────────────────────
def _visual_width(s: str) -> int:
    return sum(2 if ord(c) > 127 else 1 for c in s)


def _wrap_label(text: str, max_w: int = 18) -> list[str]:
    """Break long descriptions into at most 2 lines on / · + separators."""
    if _visual_width(text) <= max_w:
        return [text]
    for sep in [" · ", " / ", " + ", "·", "/", "+", " "]:
        if sep not in text:
            continue
        parts = text.split(sep)
        for i in range(1, len(parts)):
            left = sep.join(parts[:i])
            right = sep.join(parts[i:])
            if _visual_width(left) <= max_w and _visual_width(right) <= max_w:
                return [left, right]
        mid = max(1, len(parts) // 2)
        return [sep.join(parts[:mid]), sep.join(parts[mid:])]
    mid = len(text) // 2
    return [text[:mid], text[mid:]]


def _wrap_role(text: str, max_w: int = 22) -> list[str]:
    return _wrap_label(text, max_w)


# ── Layer left labels ───────────────────────────────────────
def layer_label(layer: int, stage: str, cn: str, en: str, desc: str, role: str) -> str:
    y0 = band_y(layer)
    h = BAND_HEIGHTS[layer]
    cx = PAD + LAYER_LABEL_W // 2
    cy = y0 + h // 2
    color = LAYER_COLORS[layer]

    desc_lines = _wrap_label(desc, max_w=18)
    role_lines = _wrap_role(role, max_w=22)

    desc_y = cy + 36
    desc_svg = (
        f'<text x="{cx}" y="{desc_y}" font-family="Helvetica" font-size="11"'
        f' fill="{DIM_LABEL}" text-anchor="middle" font-style="italic">{desc_lines[0]}</text>'
    )
    extra_y = 0
    if len(desc_lines) > 1:
        desc_svg += (
            f'<text x="{cx}" y="{desc_y + 16}" font-family="Helvetica" font-size="11"'
            f' fill="{DIM_LABEL}" text-anchor="middle" font-style="italic">{desc_lines[1]}</text>'
        )
        extra_y = 18

    # Role badge: height depends on the number of role lines
    badge_h = 26 if len(role_lines) == 1 else 40
    badge_y = cy + 56 + extra_y
    role_svg = (
        f'<rect x="{cx - 90}" y="{badge_y}" width="180" height="{badge_h}"'
        f' fill="{NODE_BG_2}" stroke="{color}" stroke-width="1" rx="13"/>'
    )
    if len(role_lines) == 1:
        role_svg += (
            f'<text x="{cx}" y="{badge_y + 18}" font-family="Helvetica" font-size="11"'
            f' font-weight="600" fill="{color}" text-anchor="middle">{role_lines[0]}</text>'
        )
    else:
        role_svg += (
            f'<text x="{cx}" y="{badge_y + 16}" font-family="Helvetica" font-size="11"'
            f' font-weight="600" fill="{color}" text-anchor="middle">{role_lines[0]}</text>'
            f'<text x="{cx}" y="{badge_y + 32}" font-family="Helvetica" font-size="11"'
            f' font-weight="600" fill="{color}" text-anchor="middle">{role_lines[1]}</text>'
        )

    return f"""
  <g>
    <rect x="{PAD}" y="{y0}" width="{LAYER_LABEL_W}" height="{h}"
          fill="{NODE_BG}" stroke="{color}" stroke-width="2" rx="14"/>
    <rect x="{PAD}" y="{y0}" width="6" height="{h}" fill="{color}" rx="3"/>
    <text x="{cx}" y="{cy - 78}" font-family="Helvetica" font-size="13"
          font-weight="700" fill="{color}" text-anchor="middle" letter-spacing="2">LAYER {layer}</text>
    <text x="{cx}" y="{cy - 54}" font-family="Helvetica" font-size="15"
          fill="{DIM_LABEL}" text-anchor="middle">{stage}</text>
    <text x="{cx}" y="{cy - 22}" font-family="Helvetica" font-size="26"
          font-weight="800" fill="{TITLE}" text-anchor="middle">{cn}</text>
    <text x="{cx}" y="{cy + 4}" font-family="Helvetica" font-size="12"
          fill="{DIM_LABEL}" text-anchor="middle">{en}</text>
    {desc_svg}
    {role_svg}
  </g>"""


def band_bg(layer: int) -> str:
    y0 = band_y(layer)
    h = BAND_HEIGHTS[layer]
    color = LAYER_COLORS[layer]
    x = PAD + LAYER_LABEL_W + 20
    bw = W - x - PAD
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


# ── Module card (full version with sub-feature list) ───────
def module_card(x: int, y: int, m: dict, color: str,
                w: int = 440, h: int = 340) -> str:
    parts = []
    parts.append(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{NODE_BG}"'
        f' stroke="{color}" stroke-width="1.6" rx="14"/>'
    )
    parts.append(
        f'<rect x="{x}" y="{y}" width="{w}" height="5" fill="{color}" rx="2.5"/>'
    )

    # Top: code badge + name + tech pill
    badge_w, badge_h = 58, 26
    parts.append(
        f'<rect x="{x + 12}" y="{y + 14}" width="{badge_w}" height="{badge_h}"'
        f' fill="{color}" rx="13"/>'
        f'<text x="{x + 12 + badge_w // 2}" y="{y + 14 + 18}"'
        f' font-family="Helvetica" font-size="13" font-weight="800"'
        f' fill="{BG}" text-anchor="middle">{m["code"]}</text>'
    )
    parts.append(
        f'<text x="{x + 12 + badge_w + 12}" y="{y + 30}"'
        f' font-family="Helvetica" font-size="17" font-weight="700"'
        f' fill="{TITLE}">{m["cn"]}</text>'
    )
    parts.append(
        f'<text x="{x + 12 + badge_w + 12}" y="{y + 46}"'
        f' font-family="Helvetica" font-size="10" fill="{DIM_LABEL}">{m["en"]}</text>'
    )
    tech = m.get("tech", "")
    if tech:
        tw = text_w(tech, 10) + 18
        parts.append(
            f'<rect x="{x + w - tw - 12}" y="{y + 16}" width="{tw}" height="20"'
            f' fill="{color}" fill-opacity="0.18" stroke="{color}"'
            f' stroke-opacity="0.55" stroke-width="1" rx="10"/>'
            f'<text x="{x + w - tw // 2 - 12}" y="{y + 30}"'
            f' font-family="Helvetica" font-size="10" font-weight="600"'
            f' fill="{color}" text-anchor="middle">{tech}</text>'
        )

    # Divider
    parts.append(
        f'<line x1="{x + 12}" y1="{y + 56}" x2="{x + w - 12}" y2="{y + 56}"'
        f' stroke="{color}" stroke-opacity="0.25" stroke-width="1"/>'
    )

    # Icon + role
    icon_size = 42
    ix, iy = x + 16, y + 66
    icon_uri = img_b64(m["icon"])
    if icon_uri:
        parts.append(
            f'<image href="{icon_uri}" x="{ix}" y="{iy}"'
            f' width="{icon_size}" height="{icon_size}"/>'
        )
    role = m["role"]
    line1, line2 = role, ""
    if len(role) > 24:
        for sep in [" / ", " · ", " , ", "·", "/"]:
            if sep in role:
                left, _, right = role.partition(sep)
                if len(left) <= 26 and len(right) <= 28:
                    line1, line2 = left, right
                    break
    rx0 = ix + icon_size + 12
    parts.append(
        f'<text x="{rx0}" y="{iy + 16}" font-family="Helvetica"'
        f' font-size="12" font-weight="600" fill="{LABEL}">{line1}</text>'
    )
    if line2:
        parts.append(
            f'<text x="{rx0}" y="{iy + 32}" font-family="Helvetica"'
            f' font-size="12" font-weight="600" fill="{LABEL}">{line2}</text>'
        )

    # IN / OUT / API
    info_y = y + 122
    rows = [
        ("IN",  m.get("in", ""),  EDGE_DATA),
        ("OUT", m.get("out", ""), LAYER_COLORS[4]),
        ("API", m.get("api", ""), EDGE_AI),
    ]
    for i, (tag, val, tag_color) in enumerate(rows):
        ry = info_y + i * 17
        if not val:
            continue
        parts.append(
            f'<rect x="{x + 12}" y="{ry - 10}" width="34" height="14"'
            f' fill="{tag_color}" fill-opacity="0.18" stroke="{tag_color}"'
            f' stroke-width="0.8" rx="3"/>'
            f'<text x="{x + 29}" y="{ry + 0}" font-family="Helvetica"'
            f' font-size="9" font-weight="700" fill="{tag_color}"'
            f' text-anchor="middle">{tag}</text>'
        )
        parts.append(
            f'<text x="{x + 52}" y="{ry + 0}" font-family="Helvetica"'
            f' font-size="10.5" fill="{LABEL}">{val}</text>'
        )

    # Sub-feature list
    sf_y = y + 188
    parts.append(
        f'<rect x="{x + 12}" y="{sf_y}" width="{w - 24}" height="{h - 188 - 14}"'
        f' fill="{NODE_BG_2}" stroke="{color}" stroke-opacity="0.4"'
        f' stroke-width="1" rx="8"/>'
    )
    parts.append(
        f'<rect x="{x + 12}" y="{sf_y}" width="{w - 24}" height="22"'
        f' fill="{color}" fill-opacity="0.18" rx="8"/>'
        f'<text x="{x + 22}" y="{sf_y + 15}" font-family="Helvetica"'
        f' font-size="10" font-weight="800" fill="{color}"'
        f' letter-spacing="1.4">▸ SUB-FEATURES</text>'
    )
    subs = m.get("subs", [])
    line_y = sf_y + 36
    for sub in subs:
        # Bullet + label
        parts.append(
            f'<circle cx="{x + 22}" cy="{line_y - 4}" r="2" fill="{color}"/>'
            f'<text x="{x + 30}" y="{line_y}" font-family="Helvetica"'
            f' font-size="10.5" fill="{LABEL}">{sub}</text>'
        )
        line_y += 17
    return "".join(parts)


# ── Cross-layer labeled data flow arrows ───────────────────
def flow_arrow(x: int, layer_from: int, label_top: str, label_bot: str,
               color: str = EDGE_DATA) -> str:
    y_top = band_y(layer_from) + BAND_HEIGHTS[layer_from]
    y_bot = band_y(layer_from + 1)
    mid_y = (y_top + y_bot) // 2
    parts = [
        f'<path d="M {x} {y_top + 2} L {x} {y_bot - 6}" stroke="{color}"'
        f' stroke-width="3" fill="none" marker-end="url(#arrow-{color[1:]})"/>'
    ]
    lw = max(text_w(label_top, 11), text_w(label_bot, 10)) + 30
    box_h = 38
    parts.append(
        f'<rect x="{x - lw // 2}" y="{mid_y - box_h // 2}" width="{lw}" height="{box_h}"'
        f' fill="{BG}" stroke="{color}" stroke-width="1.4" rx="9"/>'
        f'<text x="{x}" y="{mid_y - 3}" font-family="Helvetica" font-size="11"'
        f' font-weight="700" fill="{color}" text-anchor="middle">{label_top}</text>'
        f'<text x="{x}" y="{mid_y + 12}" font-family="Helvetica" font-size="9"'
        f' fill="{DIM_LABEL}" text-anchor="middle">{label_bot}</text>'
    )
    return "".join(parts)


def title_bar() -> str:
    return f"""
  <text x="{W // 2}" y="68" font-family="Helvetica" font-size="36"
        font-weight="800" fill="{TITLE}" text-anchor="middle">
    ReceptivIQ Platform — Business Flow Map
  </text>
  <text x="{W // 2}" y="104" font-family="Helvetica" font-size="14"
        fill="{DIM_LABEL}" text-anchor="middle">
    Customer Journey · 6 Stages · 16 Modules · Per-module: role / user / IN / OUT / API / tech + full sub-feature list
  </text>
  <text x="{W // 2}" y="130" font-family="Helvetica" font-size="11"
        fill="{DIM_LABEL}" text-anchor="middle" font-style="italic">
    Top-down: Onboarding → Data Ingestion → AI Analytics → Activation → Delivery → Governance · Cross-cutting: Compliance feedback + Audit trail
  </text>"""


def footer_panel() -> str:
    y = H - 110
    pad_x = PAD
    pw = W - PAD * 2
    parts = [
        f'<rect x="{pad_x}" y="{y}" width="{pw}" height="86"'
        f' fill="{NODE_BG}" stroke="#1F2937" stroke-width="1" rx="12"/>'
    ]
    stats = [
        ("16", "Modules"),
        ("6",  "Journey Stages"),
        ("9",  "ETL Platforms"),
        ("3",  "AI Agents"),
        ("3",  "Regulations (GDPR/CCPA/HIPAA)"),
        ("21", "FastAPI Routers"),
    ]
    sx = pad_x + 26
    for n, txt in stats:
        parts.append(
            f'<text x="{sx}" y="{y + 38}" font-family="Helvetica" font-size="26"'
            f' font-weight="800" fill="{TITLE}">{n}</text>'
            f'<text x="{sx}" y="{y + 60}" font-family="Helvetica" font-size="10"'
            f' fill="{DIM_LABEL}">{txt}</text>'
        )
        sx += 200

    items = [
        ("Stage 1–3 user / data flow", EDGE_DATA),
        ("Stage 3 → 4 AI trigger",   EDGE_AI),
        ("Stage 6 compliance feedback",        EDGE_GUARD),
        ("👤 Agency Admin",           LAYER_COLORS[1]),
        ("🏢 Client",                 LAYER_COLORS[5]),
    ]
    lx = pad_x + 26
    ly = y + 76
    parts.append(
        f'<text x="{lx}" y="{ly}" font-family="Helvetica" font-size="10"'
        f' font-weight="700" fill="{DIM_LABEL}">FLOW LEGEND  ›</text>'
    )
    lx += 110
    for label, color in items:
        parts.append(
            f'<rect x="{lx}" y="{ly - 10}" width="14" height="12" fill="{color}" rx="3"/>'
            f'<text x="{lx + 20}" y="{ly}" font-family="Helvetica" font-size="10"'
            f' fill="{LABEL}">{label}</text>'
        )
        lx += text_w(label, 10) + 50
    return "".join(parts)


# ── Business-module data (with full sub-feature list) ──────
LAYERS_DATA = [
    (1, "Stage 1", "Onboarding", "Customer Onboarding",
     "Brand intake · historical import · multi-tenant base",
     "👤 Agency Admin · 👥 Brand Manager", [
        {"code": "F13", "cn": "Brand Onboarding", "en": "Trello-style intake board",
         "icon": "client", "tech": "FastAPI · MUI",
         "role": "Trello-style board / status tracking",
         "in":  "Brand basics, contacts",
         "out": "Brand record + Onboarding tasks",
         "api": "POST /brands · /onboarding/tasks",
         "subs": [
             "Brand basics (logo · industry · target audience)",
             "Trello-style board (drag-and-drop columns)",
             "Task assignment + due date + owner",
             "Onboarding progress % (live calc)",
             "Approval workflow (submit → review → approve)",
             "BAA agreement status (HIPAA clients)",
             "Brand asset library (logo / palette / fonts)",
         ]},
        {"code": "F14", "cn": "Historical Import", "en": "3-step CSV import",
         "icon": "apacheairflow", "tech": "Celery · pandas",
         "role": "3-step: upload / map / validate",
         "in":  "CSV / Excel · historical campaign data",
         "out": "Raw warehouse rows + report",
         "api": "POST /imports · /imports/{id}/validate",
         "subs": [
             "CSV / Excel upload (≤100 MB · streaming parser)",
             "Smart field mapping (fuzzy match)",
             "Dry-run preview (first 100 rows)",
             "Failed-rows report (row number + error code)",
             "Data rollback (transactional undo)",
             "Import history diff",
             "Async progress push (WebSocket)",
         ]},
        {"code": "P0", "cn": "Platform Core", "en": "Multi-tenant + Auth",
         "icon": "auth", "tech": "JWT · OAuth2",
         "role": "Multi-tenant · auth · RBAC",
         "in":  "User email / Google OAuth",
         "out": "Access / Refresh tokens + Session",
         "api": "POST /auth/login · /auth/refresh",
         "subs": [
             "Agency multi-tenant isolation (agency_id filter)",
             "User / Role / Permission RBAC",
             "JWT + Refresh token (blacklist revocation)",
             "Google OAuth 2.0 + domain whitelist",
             "Password login + IP rate-limit (5/5min)",
             "Session timeout (HIPAA 15-min)",
             "Login lockout (15-min after fail)",
         ]},
     ]),

    (2, "Stage 2", "Data Ingestion", "ETL · Mapping · Compliance",
     "Platform data inflow · field mapping · PHI anonymization",
     "🤖 System Worker · 👤 Data Engineer", [
        {"code": "F20", "cn": "ETL Adapters", "en": "9 platform connectors",
         "icon": "celery", "tech": "Celery · Airflow",
         "role": "9 ads / CRM / attribution platforms",
         "in":  "OAuth credentials, date range",
         "out": "raw_{platform} warehouse tables",
         "api": "POST /etl/run · /etl/jobs/{id}",
         "subs": [
             "9 platform connectors (GA4 · Meta · HubSpot · DV360)",
             "（StackAdapt · LeadRX · LiveRamp · Quorum · TikTok）",
             "OAuth credentials encrypted at rest (Fernet)",
             "Incremental sync (cursor / state table)",
             "Mock mode (synthetic dev data)",
             "Failure retry (exponential backoff)",
             "Sync state tracking (success / failure / partial)",
             "DAG orchestration (Airflow scheduler)",
         ]},
        {"code": "F15", "cn": "Field Mapping", "en": "Raw → Canonical → Entity",
         "icon": "map", "tech": "dbt · SQL",
         "role": "Raw fields → Canonical → Business entity",
         "in":  "raw_* tables + mapping rules",
         "out": "Canonical schema tables",
         "api": "POST /mappings · /mappings/preview",
         "subs": [
             "Canonical schema (unified fields)",
             "4 transforms (direct / hash / lower / concat)",
             "Live preview (first 50 rows)",
             "Versioning (save → version)",
             "Mapping templates (per-platform clone)",
             "Field lineage view",
             "dbt staging → canonical → marts",
         ]},
        {"code": "C", "cn": "Compliance Layer", "en": "PHI scan + Anonymize",
         "icon": "compliance", "tech": "Fernet · SHA-256",
         "role": "PHI detector / anonymizer / IP truncate",
         "in":  "raw record (possibly containing PII/PHI)",
         "out": "Anonymized record + warning log",
         "api": "internal: phi_detector · anonymizer",
         "subs": [
             "PHI detector (HIPAA 18 identifiers scan)",
             "SHA-256 + Agency salt hashing",
             "IP truncate (IPv4 /24 · IPv6 /48)",
             "Email / phone / name anonymization",
             "No raw_json field (bypass prevention)",
             "Audit log (INSERT-only)",
             "Alert (PHI hit → notify)",
         ]},
     ]),

    (3, "Stage 3", "AI Analytics", "3 Agents · AI Brain",
     "Persona · Creative optimization · Cross-channel attribution",
     "🤖 AI Agent · 👤 Marketing Analyst", [
        {"code": "F10", "cn": "Persona Agent", "en": "Audience profiling",
         "icon": "personas", "tech": "LLM · pgvector",
         "role": "Audience segmentation + profile gen",
         "in":  "Canonical data + business goals",
         "out": "Persona profile + audience segment",
         "api": "POST /personas/generate",
         "subs": [
             "Audience clustering (K-Means + rules)",
             "LLM profile generation (humanized copy)",
             "pgvector similarity search",
             "Persona tag library (behavior / interest)",
             "A/B Persona comparison",
             "Export audience segment (→ F21)",
             "Version snapshots",
         ]},
        {"code": "F11", "cn": "Creative Agent", "en": "Creative optimization",
         "icon": "creatives", "tech": "LLM · Brand",
         "role": "Ad creative recommendations",
         "in":  "Brand voice + historical CTR",
         "out": "Creative candidates + scores",
         "api": "POST /creatives/recommend",
         "subs": [
             "Copy generation (multiple variants)",
             "Headline / description / CTA triplet",
             "CTR historical scoring",
             "Brand voice constraints",
             "A/B experiment design suggestion",
             "Creative asset library",
             "Multi-language / multi-market support",
         ]},
        {"code": "F12", "cn": "Attribution Agent", "en": "Multi-touch attribution",
         "icon": "attribution", "tech": "LLM · MTA",
         "role": "Cross-channel attribution models",
         "in":  "Touchpoints + conversion events",
         "out": "Attribution weights + channel share",
         "api": "POST /attribution/run",
         "subs": [
             "Multi-touch (MTA) models",
             "First / Last / Linear / Time-decay",
             "Cross-channel weight calculation",
             "Incremental attribution",
             "Channel ROI ranking",
             "Attribution report (PDF / JSON)",
             "LLM-generated summary",
         ]},
        {"code": "P1", "cn": "AI Brain · Warehouse", "en": "Router + Budget + Audit",
         "icon": "brain", "tech": "OpenRouter · httpx",
         "role": "Token budget / model router / audit",
         "in":  "Agent invocation request",
         "out": "LLM response + usage record",
         "api": "internal: brain.invoke()",
         "subs": [
             "Model router (Claude / Gemini per agent)",
             "Token budget control (monthly_token_budget)",
             "Usage record (token_usage table)",
             "Budget exhausted → 429 block",
             "Mock mode (when API key empty)",
             "Langfuse tracing (trace + score)",
             "Retry + fallback model",
         ]},
     ]),

    (4, "Stage 4", "Activation", "Campaigns · Audience Export",
     "Campaign mgmt · audience export to ad platforms",
     "👤 Campaign Manager · 🤖 Worker", [
        {"code": "F19", "cn": "Campaigns", "en": "Cross-platform view + Alerts",
         "icon": "googleads", "tech": "FastAPI · Celery",
         "role": "Cross-platform view + budget alerts",
         "in":  "Campaign config + budget thresholds",
         "out": "Campaign state + alert email",
         "api": "POST /campaigns · /campaigns/budget",
         "subs": [
             "Cross-platform unified view",
             "Budget config (daily / monthly / total)",
             "Spend vs budget pacing",
             "Threshold alerts (80% / 95% / 100%)",
             "Email notification (SMTP)",
             "Historical trends (CTR · CPM · ROAS)",
             "Pause / resume (API hook)",
             "Tags / groups management",
         ]},
        {"code": "F21", "cn": "Audience Export", "en": "Meta / DV360 sync",
         "icon": "audience", "tech": "Meta · DV360 SDK",
         "role": "Export to Meta / DV360 platforms",
         "in":  "Persona audience segment",
         "out": "Custom Audience ID + export job",
         "api": "POST /audiences/export",
         "subs": [
             "Meta Custom Audience push",
             "DV360 Audience push",
             "Email / phone SHA-256 hashing",
             "Async export job (Celery)",
             "Export status (success / fail / running)",
             "Quota management (daily limit)",
             "Failure rollback + retry",
         ]},
     ]),

    (5, "Stage 5", "Client Delivery", "Portal · Reports · Realtime",
     "How clients consume value: portal · PDF · realtime push",
     "🏢 Client · 👥 Stakeholder", [
        {"code": "F16", "cn": "Client Portal", "en": "Login + Dashboard",
         "icon": "portal", "tech": "React · MUI",
         "role": "Client login + dashboard",
         "in":  "Client credentials (scoped token)",
         "out": "Dashboard + download links",
         "api": "GET /portal/dashboard · /portal/reports",
         "subs": [
             "Client login (scoped token)",
             "Dashboard (KPI · campaigns · reports)",
             "Report download list (PDF / Excel)",
             "Historical archive search",
             "Notification center (with F17)",
             "Multi-brand switcher (Agency)",
             "Dark / light theme",
             "Responsive web (desktop + tablet)",
         ]},
        {"code": "F22", "cn": "PDF Reports", "en": "Template + async + email",
         "icon": "pdf_report", "tech": "WeasyPrint · Celery",
         "role": "Template render / async gen / email",
         "in":  "Report template + data range",
         "out": "PDF file + MinIO/S3 URL",
         "api": "POST /reports · /reports/{id}/download",
         "subs": [
             "Report template library (quarterly / monthly / weekly)",
             "WeasyPrint HTML → PDF rendering",
             "Celery async generation (avoid blocking)",
             "MinIO (dev) / S3 (prod) storage",
             "Email delivery (SMTP + attachment / download link)",
             "Signed download link (time-limited URL)",
             "PDF encryption (optional · client password)",
             "Report watermark (Brand logo)",
         ]},
        {"code": "F17", "cn": "Realtime Notifications", "en": "WebSocket push + history",
         "icon": "ws", "tech": "WebSocket · Redis",
         "role": "WebSocket /ws push + history",
         "in":  "System events (import complete · budget alert)",
         "out": "Realtime push + notification list",
         "api": "WS /ws · GET /notifications",
         "subs": [
             "WebSocket /ws long connection",
             "Event types (import · alert · report-ready)",
             "Read / unread state",
             "History replay (reconnect catch-up)",
             "Redis Pub/Sub relay",
             "Browser desktop notification API",
             "Email fallback (critical events)",
         ]},
     ]),

    (6, "Stage 6", "Governance", "Observability · Compliance · Audit",
     "Continuous compliance · full observability · audit trail",
     "👤 Admin · 🛡 Compliance Officer", [
        {"code": "F18", "cn": "Observability", "en": "Langfuse · Sentry · Health",
         "icon": "langfuse", "tech": "Langfuse · Sentry",
         "role": "LLM trace / error monitor / health",
         "in":  "Application logs / LLM calls / error events",
         "out": "Trace · Issue · health metrics",
         "api": "GET /health · /metrics",
         "subs": [
             "Langfuse LLM trace (1 trace per call)",
             "Sentry error aggregation + notification",
             "/health checks (DB · Redis · LLM)",
             "/metrics Prometheus format",
             "Slow query trace (>200ms auto-log)",
             "Custom business metrics (DAU · jobs)",
             "Audit log (action · resource · time)",
         ]},
        {"code": "C+", "cn": "Compliance · DSAR", "en": "GDPR/CCPA/HIPAA + DSAR",
         "icon": "compliance", "tech": "Fernet · Audit-Only",
         "role": "GDPR / CCPA / HIPAA + DSAR + retention",
         "in":  "DSAR requests / retention policies / violation events",
         "out": "Export/delete/notify + audit",
         "api": "POST /dsar · GET /audit/logs",
         "subs": [
             "DSAR (access · delete · export · rectify)",
             "DSAR SLA (GDPR 30d / CCPA 45d / HIPAA 30d)",
             "Retention policies (strictest: audit 6y)",
             "Audit log (6y INSERT-only · immutable)",
             "Breach notification (GDPR 72h / HIPAA 60d)",
             "BAA status + expiry alert",
             "Encryption key rotation (per-Agency key)",
             "Data minimization policy",
         ]},
     ]),
]


def build_svg() -> str:
    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"'
        f' viewBox="0 0 {W} {H}">'
    )
    parts.append(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
    parts.append(
        '<defs><pattern id="dots" width="36" height="36" patternUnits="userSpaceOnUse">'
        '<circle cx="2" cy="2" r="1" fill="#1E293B"/></pattern></defs>'
        f'<rect width="{W}" height="{H}" fill="url(#dots)" opacity="0.4"/>'
    )
    arrow_defs = '<defs>'
    for color in [EDGE_DATA, EDGE_USER, EDGE_AI, EDGE_GUARD,
                  LAYER_COLORS[1], LAYER_COLORS[2], LAYER_COLORS[3],
                  LAYER_COLORS[4], LAYER_COLORS[5], LAYER_COLORS[6]]:
        cid = color[1:]
        arrow_defs += (
            f'<marker id="arrow-{cid}" viewBox="0 0 10 10" refX="9" refY="5"'
            f' markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{color}"/></marker>'
        )
    arrow_defs += '</defs>'
    parts.append(arrow_defs)
    parts.append(title_bar())

    for (n, en_stage, cn_name, en_name, desc, role, modules) in LAYERS_DATA:
        parts.append(band_bg(n))
        parts.append(layer_label(n, en_stage, cn_name, en_name, desc, role))
        avail_w = W - (PAD + LAYER_LABEL_W + 20) - PAD - 40
        x0 = PAD + LAYER_LABEL_W + 40
        nm = len(modules)
        max_w = CARD_MAX_W_BY_N.get(nm, 460)
        card_w = min(max_w, (avail_w - (nm - 1) * CARD_GAP) // nm)
        gap = CARD_GAP
        total_w = nm * card_w + (nm - 1) * gap
        start_x = x0 + (avail_w - total_w) // 2
        y_card = band_y(n) + 20
        card_h = BAND_HEIGHTS[n] - 40
        for i, m in enumerate(modules):
            cx = start_x + i * (card_w + gap)
            parts.append(module_card(cx, y_card, m, LAYER_COLORS[n],
                                     w=card_w, h=card_h))

    # Inter-layer data-flow arrows (centered in the band gap, slight right offset)
    flow_x = W // 2 + 280
    flow_defs = [
        (1, "Kickoff",         "Brand · Historical · Creds", LAYER_COLORS[1]),
        (2, "Raw data loaded", "raw_* · Canonical · Anon.",  EDGE_DATA),
        (3, "AI insights",     "Persona · Creative · Attr.", EDGE_AI),
        (4, "Activation done", "Campaign · Audience ID",     LAYER_COLORS[4]),
        (5, "Delivered",       "Portal · PDF · Realtime",    LAYER_COLORS[5]),
    ]
    for (lf, top, bot, col) in flow_defs:
        parts.append(flow_arrow(flow_x, lf, top, bot, col))

    # Compliance feedback loop: routed via the left channel, label sits in the L5→L6 gap
    gov_x = PAD + LAYER_LABEL_W + 10
    y_l6_top = band_y(6) - 4
    y_l2_top = band_y(2) + 8
    parts.append(
        f'<path d="M {gov_x} {y_l6_top} L {gov_x} {y_l2_top}"'
        f' stroke="{EDGE_GUARD}" stroke-width="1.8" fill="none" stroke-dasharray="7 5"'
        f' opacity="0.75" marker-end="url(#arrow-{EDGE_GUARD[1:]})"/>'
    )
    label_y = band_y(6) - BAND_GAP // 2
    parts.append(
        f'<rect x="{gov_x - 96}" y="{label_y - 18}" width="192" height="36"'
        f' fill="{BG}" stroke="{EDGE_GUARD}" stroke-width="1.4" rx="9"/>'
        f'<text x="{gov_x}" y="{label_y - 2}" font-family="Helvetica" font-size="12"'
        f' font-weight="700" fill="{EDGE_GUARD}"'
        f' text-anchor="middle">↺ Compliance Feedback</text>'
        f'<text x="{gov_x}" y="{label_y + 12}" font-family="Helvetica" font-size="9"'
        f' fill="{DIM_LABEL}" text-anchor="middle">DSAR · Retention · Breach notice</text>'
    )

    parts.append(footer_panel())
    parts.append('</svg>')
    return "\n".join(parts)


def main() -> None:
    svg = build_svg()
    out_svg = ROOT / "business-flow-layered-en.svg"
    out_svg.write_text(svg)
    print(f"✓ wrote {out_svg.name} ({len(svg):,} bytes)")
    out_png = ROOT / "business-flow-layered-en.png"
    try:
        subprocess.run(
            ["rsvg-convert", str(out_svg), "-o", str(out_png), "-w", str(W)],
            check=True, capture_output=True
        )
        print(f"✓ wrote {out_png.name} via rsvg-convert")
    except FileNotFoundError:
        print("rsvg-convert not found")
    except subprocess.CalledProcessError as e:
        print(f"rsvg-convert failed: {e.stderr.decode()}")


if __name__ == "__main__":
    main()
