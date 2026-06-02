#!/usr/bin/env python3
"""ReceptivIQ Platform — Frontend Feature Map

Frontend pages and sub-components organized by user journey layer:
  Public entry → Workspace → Data UI → AI workbench → Marketing delivery → Client portal + admin

Each module labels: route · user · entry · main action · key APIs · UI sub-component list.
"""
from __future__ import annotations
import base64
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
ICONS = ROOT / "icons"

# Theme
BG          = "#0B1220"
NODE_BG     = "#111B2D"
NODE_BG_2   = "#0F1729"
TITLE       = "#F8FAFC"
LABEL       = "#E2E8F0"
DIM_LABEL   = "#94A3B8"
EDGE_DATA   = "#22D3EE"
EDGE_USER   = "#A78BFA"
EDGE_AI     = "#F472B6"
EDGE_GUARD  = "#F59E0B"

# Frontend palette: screen/UI flavor, distinct from the business-flow map
LAYER_COLORS = {
    1: "#0EA5E9",   # Public entry — sky
    2: "#6366F1",   # Workspace — indigo
    3: "#14B8A6",   # Data UI — teal
    4: "#A855F7",   # AI workbench — purple
    5: "#F97316",   # Marketing delivery — orange
    6: "#F43F5E",   # Client portal + admin — rose
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


# ── Module card (with UI sub-component list) ───────────────
def module_card(x: int, y: int, m: dict, color: str,
                w: int = 440, h: int = 360) -> str:
    parts = []
    parts.append(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{NODE_BG}"'
        f' stroke="{color}" stroke-width="1.6" rx="14"/>'
    )
    parts.append(
        f'<rect x="{x}" y="{y}" width="{w}" height="5" fill="{color}" rx="2.5"/>'
    )
    # Screen corner glyph (window-control dot decoration)
    for i, dot_color in enumerate(["#F87171", "#FBBF24", "#34D399"]):
        parts.append(
            f'<circle cx="{x + w - 18 - i * 12}" cy="{y + 16}" r="3.5"'
            f' fill="{dot_color}" opacity="0.7"/>'
        )

    # Top: route badge + name + role label
    route = m.get("route", m.get("code", ""))
    rw = text_w(route, 12) + 18
    parts.append(
        f'<rect x="{x + 12}" y="{y + 14}" width="{rw}" height="26"'
        f' fill="{color}" rx="13"/>'
        f'<text x="{x + 12 + rw // 2}" y="{y + 14 + 18}"'
        f' font-family="Menlo,Helvetica" font-size="12" font-weight="700"'
        f' fill="{BG}" text-anchor="middle">{route}</text>'
    )
    parts.append(
        f'<text x="{x + 12 + rw + 12}" y="{y + 30}"'
        f' font-family="Helvetica" font-size="16" font-weight="700"'
        f' fill="{TITLE}">{m["cn"]}</text>'
    )
    parts.append(
        f'<text x="{x + 12 + rw + 12}" y="{y + 46}"'
        f' font-family="Helvetica" font-size="10" fill="{DIM_LABEL}">{m["en"]}</text>'
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
    if len(role) > 22:
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

    # ENTRY / ACTIONS / API
    info_y = y + 122
    rows = [
        ("ENTRY",   m.get("entry", ""),   EDGE_USER),
        ("ACTIONS", m.get("actions", ""), LAYER_COLORS[5]),
        ("API",     m.get("api", ""),     EDGE_AI),
    ]
    for i, (tag, val, tag_color) in enumerate(rows):
        ry = info_y + i * 17
        if not val:
            continue
        tag_w = 46
        parts.append(
            f'<rect x="{x + 12}" y="{ry - 10}" width="{tag_w}" height="14"'
            f' fill="{tag_color}" fill-opacity="0.18" stroke="{tag_color}"'
            f' stroke-width="0.8" rx="3"/>'
            f'<text x="{x + 12 + tag_w // 2}" y="{ry + 0}" font-family="Helvetica"'
            f' font-size="9" font-weight="700" fill="{tag_color}"'
            f' text-anchor="middle">{tag}</text>'
        )
        parts.append(
            f'<text x="{x + 12 + tag_w + 6}" y="{ry + 0}" font-family="Helvetica"'
            f' font-size="10.5" fill="{LABEL}">{val}</text>'
        )

    # Sub-component list
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
        f' letter-spacing="1.4">▸ UI COMPONENTS</text>'
    )
    line_y = sf_y + 36
    for sub in m.get("subs", []):
        parts.append(
            f'<circle cx="{x + 22}" cy="{line_y - 4}" r="2" fill="{color}"/>'
            f'<text x="{x + 30}" y="{line_y}" font-family="Helvetica"'
            f' font-size="10.5" fill="{LABEL}">{sub}</text>'
        )
        line_y += 17
    return "".join(parts)


# ── Cross-layer labeled flow arrows ───────────────────────
def flow_arrow(x: int, layer_from: int, label_top: str, label_bot: str,
               color: str = EDGE_USER) -> str:
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
    ReceptivIQ Platform — Frontend Feature Map
  </text>
  <text x="{W // 2}" y="104" font-family="Helvetica" font-size="14"
        fill="{DIM_LABEL}" text-anchor="middle">
    User Journey · 6 Layers · 21 Pages/Modules · Per-page route / entry / actions / API + UI components
  </text>
  <text x="{W // 2}" y="130" font-family="Helvetica" font-size="11"
        fill="{DIM_LABEL}" text-anchor="middle" font-style="italic">
    Top-down: Public Entry → Workspace → Data UI → AI Workspace → Activation · Delivery → Client · Admin
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
        ("21", "Pages / Modules"),
        ("6",  "User-journey Layers"),
        ("React 19", "+ TypeScript"),
        ("MUI v5", "UI Library (MUI)"),
        ("Vite", "Dev Server + Build"),
        ("⌘K", "Command Palette"),
    ]
    sx = pad_x + 26
    for n, txt in stats:
        parts.append(
            f'<text x="{sx}" y="{y + 38}" font-family="Helvetica" font-size="22"'
            f' font-weight="800" fill="{TITLE}">{n}</text>'
            f'<text x="{sx}" y="{y + 60}" font-family="Helvetica" font-size="10"'
            f' fill="{DIM_LABEL}">{txt}</text>'
        )
        sx += 220

    items = [
        ("User Navigation Flow",   EDGE_USER),
        ("AI trigger",                 EDGE_AI),
        ("Data fetch",                EDGE_DATA),
        ("👤 Agency / Brand",       LAYER_COLORS[2]),
        ("🏢 Client (restricted)",  LAYER_COLORS[6]),
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


# ── Frontend module data ────────────────────────────────────
LAYERS_DATA = [
    (1, "Layer 1", "Public Entry", "Auth · Entry Pages",
     "Pre-auth entry: sign-in / reset / client portal",
     "🌐 Public access", [
        {"route": "/login", "cn": "Sign-in", "en": "Email + Google OAuth",
         "icon": "auth", "role": "Email login / Google OAuth",
         "entry": "Unauthenticated access → redirect",
         "actions": "Sign in → land on home",
         "api": "POST /auth/login · /auth/google",
         "subs": [
             "Email + password form",
             "「Sign in with Google」 button",
             "Password strength hint",
             "Failed attempts counter (5 → lockout)",
             "「Remember me」 checkbox",
             "「Forgot password」 link",
             "Inline error display",
         ]},
        {"route": "/reset-password", "cn": "Reset Password", "en": "Forgot + Email Verify",
         "icon": "smtp", "role": "Forgot password / email verify",
         "entry": "「Forgot password」 link on sign-in",
         "actions": "Send reset mail / set new password",
         "api": "POST /auth/forgot · /auth/reset",
         "subs": [
             "Email input → reset link",
             "Mail contains one-time token",
             "New password + confirm fields",
             "Live password strength check",
             "Success → redirect to sign-in",
             "Token-expired error handling",
         ]},
        {"route": "/client/login", "cn": "Client Portal Login", "en": "Standalone Entry",
         "icon": "portal", "role": "Client-side login entry",
         "entry": "Portal link in client email",
         "actions": "Sign in → client dashboard",
         "api": "POST /portal/auth/login",
         "subs": [
             "Standalone page (Brand logo)",
             "Email + one-time PIN",
             "Brand picker (when multiple)",
             "Privacy / cookie notice",
             "「← Back to ReceptivIQ」 link",
             "Scoped token (24h expiry)",
         ]},
     ]),

    (2, "Layer 2", "Workspace", "Dashboard · Nav · Search",
     "Main workspace: home · navigation · command palette",
     "👤 Agency Admin · Brand Manager", [
        {"route": "/", "cn": "Home Dashboard", "en": "KPI Overview + Quick Actions",
         "icon": "dashboard", "role": "KPI overview / quick entry",
         "entry": "Default page after sign-in",
         "actions": "View KPIs / jump to modules",
         "api": "GET /dashboard · /campaigns/summary",
         "subs": [
             "KPI cards (campaigns · audience · reports · budget)",
             "Recent activity timeline (newest first)",
             "Task panel (onboarding · approvals)",
             "Quick actions (new campaign / import)",
             "Last-updated timestamp",
             "Multi-Brand switcher",
             "Today's spend overview",
         ]},
        {"route": "<Sidebar/>", "cn": "Global Navigation", "en": "Sidebar + Topbar",
         "icon": "react", "role": "Sidebar + topbar + switcher",
         "entry": "All authenticated pages",
         "actions": "Switch Brand / page / theme",
         "api": "GET /me · /brands/me",
         "subs": [
             "Sidebar (collapsible · multi-level)",
             "Topbar (search · notify · avatar)",
             "Brand switcher (multi-brand Agency)",
             "Theme toggle (dark / light)",
             "Notification badge (dot + count)",
             "User menu (settings / sign-out)",
             "Breadcrumb",
         ]},
        {"route": "⌘K", "cn": "Command Palette", "en": "Global Quick Search",
         "icon": "vite", "role": "Global quick search",
         "entry": "⌘K / Ctrl+K shortcut",
         "actions": "Search entities / trigger actions",
         "api": "GET /search?q=",
         "subs": [
             "⌘K opens command palette",
             "Types: Brand · Campaign · Persona · Report",
             "Fuzzy match + keyword highlight",
             "Recent items list",
             "Quick actions (「New campaign」 etc.)",
             "Keyboard nav (↑↓ Enter Esc)",
         ]},
     ]),

    (3, "Layer 3", "Data UI", "Brand · Import · ETL · Mapping",
     "Data pages: board · wizard · connections · mapping editor",
     "👤 Data Engineer · Brand Manager", [
        {"route": "/brands/:id", "cn": "Brand Onboarding Board", "en": "Trello-style Board",
         "icon": "client", "role": "Trello-style drag-and-drop board",
         "entry": "Auto redirect after new Brand created",
         "actions": "Drag tasks / approve / complete onboarding",
         "api": "GET /brands/:id · POST /brands/:id/tasks",
         "subs": [
             "Trello board (todo / doing / done)",
             "Drag-and-drop columns (react-dnd)",
             "Task detail side-drawer",
             "Assignee + due date",
             "Approval flow (submit → approve)",
             "Top progress bar (% completion)",
             "BAA upload area (HIPAA)",
             "Brand asset library (logo / palette)",
         ]},
        {"route": "/imports/new", "cn": "Import Wizard", "en": "3-step CSV Import",
         "icon": "apacheairflow", "role": "3-step: upload / map / validate",
         "entry": "Home quick-action / Data menu",
         "actions": "Import data → write warehouse",
         "api": "POST /imports · /imports/{id}/validate",
         "subs": [
             "Step 1: upload CSV / Excel (≤100 MB)",
             "Step 2: field mapping + smart auto-match",
             "Step 3: dry-run preview (first 100 rows)",
             "File type + size validation",
             "Progress bar + WebSocket live feedback",
             "Failed-rows table (row number + error code)",
             "Rollback button (after a failed import)",
             "Import history diff",
         ]},
        {"route": "/etl/connections", "cn": "ETL Connections", "en": "9 Platforms OAuth",
         "icon": "celery", "role": "9 platforms OAuth authorization",
         "entry": "Data menu / Settings",
         "actions": "Authorize / sync / view logs",
         "api": "GET /etl/connections · POST /etl/run",
         "subs": [
             "9 platform cards (GA4 / Meta / HubSpot / DV360 …)",
             "OAuth 「Connect」 button",
             "Credential status (valid / expiring)",
             "Last sync time + status",
             "Manual sync trigger",
             "Sync history log panel",
             "Retry + error detail",
         ]},
        {"route": "/mappings/:id", "cn": "Field Mapping Editor", "en": "Drag-and-drop Mapping",
         "icon": "map", "role": "Drag mapping / transforms / preview",
         "entry": "Data menu / after ETL sync",
         "actions": "Save mapping / publish version",
         "api": "POST /mappings · /mappings/preview",
         "subs": [
             "Left: raw field list",
             "Right: Canonical schema",
             "Drag-to-connect + match highlight",
             "Transform dropdown (direct/hash/lower/concat)",
             "Live preview (first 50 rows)",
             "Version dropdown switcher",
             "Save + apply buttons",
             "Field lineage visualization",
         ]},
     ]),

    (4, "Layer 4", "AI Workspace", "Persona · Creative · Attribution · Settings",
     "3 AI agent workspaces + model settings",
     "👤 Marketing Analyst · 🤖 AI", [
        {"route": "/personas", "cn": "Persona Library", "en": "List + Generate + Detail",
         "icon": "personas", "role": "List / generate / detail",
         "entry": "AI menu / Home KPI jump",
         "actions": "Create / edit / export audience",
         "api": "GET /personas · POST /personas/generate",
         "subs": [
             "Persona card grid + tag filter",
             "Create wizard (goal + data range)",
             "Generation loading animation (streaming)",
             "Detail panel (attributes + description)",
             "A/B comparison split view",
             "「Export to Meta / DV360」 button",
             "Version snapshots",
             "pgvector similar-persona recommendations",
         ]},
        {"route": "/creatives", "cn": "Creative Browser", "en": "Ad Creative Candidates",
         "icon": "creatives", "role": "Ad creative candidate browser",
         "entry": "AI menu / Campaign detail",
         "actions": "Pick creative / build A/B test",
         "api": "GET /creatives · POST /creatives/recommend",
         "subs": [
             "Creative grid (image + copy)",
             "Sort by CTR score",
             "Headline / description / CTA triplet",
             "Brand-voice chips",
             "「New A/B test」 button",
             "Multi-language switcher",
             "Variant history comparison",
         ]},
        {"route": "/attribution", "cn": "Attribution Analytics", "en": "Cross-channel Attribution",
         "icon": "attribution", "role": "Cross-channel attribution viz",
         "entry": "AI menu / Campaign detail",
         "actions": "Pick model / export report",
         "api": "POST /attribution/run",
         "subs": [
             "Model picker (First/Last/Linear/Time-decay/MTA)",
             "Touchpoint timeline view",
             "Channel contribution pie",
             "Channel ROI ranking table",
             "LLM summary paragraph (auto)",
             "「Export PDF」 button",
             "Incremental attribution toggle",
         ]},
        {"route": "/settings/ai", "cn": "AI Settings", "en": "Router + Budget",
         "icon": "brain", "role": "Model router + budget",
         "entry": "Settings menu",
         "actions": "Switch model / adjust budget",
         "api": "GET/POST /settings/ai",
         "subs": [
             "Per-agent model router dropdowns",
             "Claude / Gemini options",
             "Monthly token budget input",
             "Current usage progress bar",
             "Alert thresholds (80% / 95%)",
             "Mock mode toggle (dev)",
             "Langfuse trace link",
         ]},
     ]),

    (5, "Layer 5", "Activation · Delivery", "Campaign · Audience · Report",
     "Campaign mgmt · audience export · PDF reports",
     "👤 Campaign Manager", [
        {"route": "/campaigns", "cn": "Campaigns", "en": "Cross-platform + Budget",
         "icon": "googleads", "role": "Cross-platform + budget",
         "entry": "Home / Marketing menu",
         "actions": "Create / pause / adjust budget",
         "api": "GET/POST /campaigns · /campaigns/budget",
         "subs": [
             "Campaign list (DataGrid sort / filter)",
             "Multi-platform unified view (GA4 / Meta / DV360)",
             "Detail side-drawer",
             "Budget config (daily / monthly / total)",
             "Pacing line chart (spend vs budget)",
             "Threshold alerts (80 / 95 / 100%)",
             "Pause / resume buttons",
             "Tags + groups",
         ]},
        {"route": "/audiences/export", "cn": "Audience Export", "en": "Meta / DV360 Push",
         "icon": "audience", "role": "Meta / DV360 audience push",
         "entry": "Persona detail / Audience menu",
         "actions": "Push audience / view jobs",
         "api": "POST /audiences/export",
         "subs": [
             "Pick Persona audience segment",
             "Platform pick (Meta CA / DV360 Aud.)",
             "Hash preview (email → SHA-256)",
             "Async job progress bar",
             "Export history list",
             "Retry button",
             "Quota remaining display",
         ]},
        {"route": "/reports", "cn": "PDF Reports", "en": "Template + Async + Email",
         "icon": "pdf_report", "role": "Template render + async gen",
         "entry": "Home / Reports menu",
         "actions": "Pick template / generate / deliver",
         "api": "POST /reports · GET /reports/{id}/download",
         "subs": [
             "Template library (quarterly / monthly / weekly / custom)",
             "Date-range picker (date / brand / campaign)",
             "Live HTML preview",
             "\"Generate PDF\" button (async + queue)",
             "Task queue status",
             "Signed download link (time-limited)",
             "\"Email to client\" button",
             "Report watermark (Brand logo)",
         ]},
     ]),

    (6, "Layer 6", "Client · Admin", "Portal · Users · Compliance · Health",
     "Client portal + admin + compliance + monitoring",
     "🏢 Client · 👤 Admin · 🛡 Officer", [
        {"route": "/client/*", "cn": "Client Portal", "en": "Standalone Client View",
         "icon": "portal", "role": "Standalone client view (scoped)",
         "entry": "Portal link in client email",
         "actions": "View KPIs / download reports / receive notify",
         "api": "GET /portal/dashboard · /portal/reports",
         "subs": [
             "Brand-styled colors + logo",
             "Scoped dashboard (read-only)",
             "Campaign overview (KPIs)",
             "Report download list (signed URLs)",
             "Notification center (WebSocket)",
             "Multi-brand picker (if any)",
             "Dark / light theme",
             "Privacy / cookie settings",
         ]},
        {"route": "/settings/users", "cn": "User Management", "en": "Agency Users + Roles",
         "icon": "staff", "role": "Agency users + roles",
         "entry": "Settings menu",
         "actions": "Invite / change role / disable",
         "api": "GET/POST /users · /roles",
         "subs": [
             "User list (DataGrid)",
             "Invite user (email + role)",
             "Role management (preset + custom)",
             "Permission matrix view",
             "Disable / enable toggle",
             "Last login time",
             "Force sign-out button",
         ]},
        {"route": "/compliance", "cn": "Compliance Center", "en": "DSAR + Audit Log",
         "icon": "compliance", "role": "DSAR + audit log",
         "entry": "Settings menu / compliance alert",
         "actions": "Process DSAR / search audit",
         "api": "POST /dsar · GET /audit/logs",
         "subs": [
             "DSAR list (access · delete · export · rectify)",
             "SLA countdown (30d / 45d)",
             "Audit log search (user / resource / time)",
             "6-year archive view",
             "BAA status card",
             "Retention policy config",
             "Breach event registry",
         ]},
        {"route": "/admin/health", "cn": "System Health", "en": "Status + Metrics",
         "icon": "langfuse", "role": "Service status + metrics",
         "entry": "Settings menu / topbar status dot",
         "actions": "View status / jump to alerts",
         "api": "GET /health · /metrics",
         "subs": [
             "Service status cards (DB · Redis · LLM)",
             "Live health metrics chart",
             "Slow query list",
             "Langfuse trace link",
             "Sentry issue list",
             "System resource usage",
             "Manual alert test button",
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

    # Inter-layer user journey arrows
    flow_x = W // 2 + 280
    flow_defs = [
        (1, "Signed in",       "JWT · Session established",  LAYER_COLORS[1]),
        (2, "Enter workspace", "Brand · Campaign · Persona", EDGE_USER),
        (3, "Data ready",      "raw_* loaded · mapping done", EDGE_DATA),
        (4, "AI insights",     "Persona · Creative · Attr.", EDGE_AI),
        (5, "Activation done", "Campaign · Report · Aud. ID", LAYER_COLORS[5]),
    ]
    for (lf, top, bot, col) in flow_defs:
        parts.append(flow_arrow(flow_x, lf, top, bot, col))

    # Client portal feedback loop: from L6 client portal back to L5 (dashed)
    cp_x = PAD + LAYER_LABEL_W + 10
    y_l6_top = band_y(6) - 4
    y_l5_top = band_y(5) + 8
    parts.append(
        f'<path d="M {cp_x} {y_l6_top} L {cp_x} {y_l5_top}"'
        f' stroke="{LAYER_COLORS[6]}" stroke-width="1.8" fill="none" stroke-dasharray="7 5"'
        f' opacity="0.75" marker-end="url(#arrow-{LAYER_COLORS[6][1:]})"/>'
    )
    label_y = band_y(6) - BAND_GAP // 2
    parts.append(
        f'<rect x="{cp_x - 92}" y="{label_y - 18}" width="184" height="36"'
        f' fill="{BG}" stroke="{LAYER_COLORS[6]}" stroke-width="1.4" rx="9"/>'
        f'<text x="{cp_x}" y="{label_y - 2}" font-family="Helvetica" font-size="12"'
        f' font-weight="700" fill="{LAYER_COLORS[6]}"'
        f' text-anchor="middle">↺ Client Feedback Loop</text>'
        f'<text x="{cp_x}" y="{label_y + 12}" font-family="Helvetica" font-size="9"'
        f' fill="{DIM_LABEL}" text-anchor="middle">View reports · Notifications · Feedback</text>'
    )

    parts.append(footer_panel())
    parts.append('</svg>')
    return "\n".join(parts)


def main() -> None:
    svg = build_svg()
    out_svg = ROOT / "frontend-feature-layered-en.svg"
    out_svg.write_text(svg)
    print(f"✓ wrote {out_svg.name} ({len(svg):,} bytes)")
    out_png = ROOT / "frontend-feature-layered-en.png"
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
