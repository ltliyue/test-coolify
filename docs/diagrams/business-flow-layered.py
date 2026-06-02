#!/usr/bin/env python3
"""ReceptivIQ Platform — 业务功能流程图 (Business Flow Map · 完整子功能版)

6 层客户旅程视图，每个模块详注：
  · 角色 · 用户 · 输入 · 输出 · API · 技术栈
  · 完整子功能清单 (Sub-features)
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

# 卡片布局参数：按模块数动态选 max 宽度，让各层视觉宽度接近
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


# ── 分层左标签（自动换行）───────────────────────────────────
def _visual_width(s: str) -> int:
    return sum(2 if ord(c) > 127 else 1 for c in s)


def _wrap_label(text: str, max_w: int = 18) -> list[str]:
    """把长描述拆成最多 2 行，按 / · + 等分隔符断行。"""
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


# ── 分层左标签 ───────────────────────────────────────────────
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

    # 角色徽章：根据 role 行数决定高度
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


# ── 模块卡片（完整版，含子功能清单）──────────────────────────
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

    # 顶部：code 徽章 + 名称 + tech 胶囊
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

    # 分割线
    parts.append(
        f'<line x1="{x + 12}" y1="{y + 56}" x2="{x + w - 12}" y2="{y + 56}"'
        f' stroke="{color}" stroke-opacity="0.25" stroke-width="1"/>'
    )

    # 图标 + 角色
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

    # 子功能清单
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
        f' letter-spacing="1.4">▸ 子功能 SUB-FEATURES</text>'
    )
    subs = m.get("subs", [])
    line_y = sf_y + 36
    for sub in subs:
        # 圆点 + 文字
        parts.append(
            f'<circle cx="{x + 22}" cy="{line_y - 4}" r="2" fill="{color}"/>'
            f'<text x="{x + 30}" y="{line_y}" font-family="Helvetica"'
            f' font-size="10.5" fill="{LABEL}">{sub}</text>'
        )
        line_y += 17
    return "".join(parts)


# ── 跨层带标签数据流箭头 ─────────────────────────────────────
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
    ReceptivIQ Platform — 业务功能流程图 (Business Flow Map)
  </text>
  <text x="{W // 2}" y="104" font-family="Helvetica" font-size="14"
        fill="{DIM_LABEL}" text-anchor="middle">
    Customer Journey · 6 阶段 · 16 功能模块 · 每模块详注角色/用户/输入/输出/API/技术栈 + 完整子功能清单
  </text>
  <text x="{W // 2}" y="130" font-family="Helvetica" font-size="11"
        fill="{DIM_LABEL}" text-anchor="middle" font-style="italic">
    自上而下：客户入驻 → 数据接入 → AI 分析 → 营销执行 → 客户交付 → 平台治理 · 横切：合规反馈环 + 审计追溯
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
        ("16", "功能模块 Modules"),
        ("6",  "客户旅程阶段 Stages"),
        ("9",  "ETL 平台 Platforms"),
        ("3",  "AI Agent"),
        ("3",  "合规法规 GDPR/CCPA/HIPAA"),
        ("21", "FastAPI Router"),
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
        ("Stage 1–3 用户/数据 Flow", EDGE_DATA),
        ("Stage 3 → 4 AI Trigger",   EDGE_AI),
        ("Stage 6 合规反馈环",        EDGE_GUARD),
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


# ── 业务模块数据（含完整子功能清单）──────────────────────────
LAYERS_DATA = [
    (1, "Onboarding", "客户入驻", "Customer Onboarding",
     "Brand 信息 + 历史数据 + 多租户基础",
     "👤 Agency Admin · 👥 Brand Manager", [
        {"code": "F13", "cn": "品牌入驻", "en": "Brand Onboarding",
         "icon": "client", "tech": "FastAPI · MUI",
         "role": "Trello 风格看板 / 项目状态追踪",
         "in":  "Brand 基础信息、联系人",
         "out": "Brand 记录 + Onboarding Tasks",
         "api": "POST /brands · /onboarding/tasks",
         "subs": [
             "品牌基础信息（Logo · 行业 · 目标受众）",
             "Trello 风格看板视图（拖拽 + 列分组）",
             "任务分配 + 截止日期 + 责任人",
             "入驻进度百分比（实时计算）",
             "审批工作流（提交 → 复核 → 通过）",
             "BAA 协议状态追踪（HIPAA 客户必备）",
             "品牌素材库（Logo / 调色板 / 字体）",
         ]},
        {"code": "F14", "cn": "历史数据导入", "en": "Historical Import",
         "icon": "apacheairflow", "tech": "Celery · pandas",
         "role": "三步导入：上传 / 映射 / 验证",
         "in":  "CSV / Excel · 历史活动数据",
         "out": "Raw warehouse 记录 + 验证报告",
         "api": "POST /imports · /imports/{id}/validate",
         "subs": [
             "CSV / Excel 上传（≤100MB · 流式解析）",
             "智能字段匹配（fuzzy match）",
             "Dry-run 预览（前 100 行）",
             "失败行报告（行号 + 错误码）",
             "数据回滚（事务级 undo）",
             "历史导入版本对比",
             "异步进度推送（WebSocket）",
         ]},
        {"code": "P0", "cn": "平台核心", "en": "Platform Core",
         "icon": "auth", "tech": "JWT · OAuth2",
         "role": "多租户 + 鉴权 + RBAC",
         "in":  "用户邮箱 / Google OAuth",
         "out": "Access/Refresh Token + Session",
         "api": "POST /auth/login · /auth/refresh",
         "subs": [
             "Agency 多租户隔离（agency_id 强制过滤）",
             "User / Role / Permission RBAC",
             "JWT + Refresh Token（黑名单回收）",
             "Google OAuth 2.0 + 域名白名单",
             "密码登录 + IP 限流（5 次/5 分钟）",
             "Session 超时（HIPAA 15 分钟）",
             "登录失败锁定（15 分钟）",
         ]},
     ]),

    (2, "Data Ingestion", "数据接入", "ETL · Mapping · Compliance",
     "原始数据流入 + 字段映射 + PHI 匿名化",
     "🤖 System Worker · 👤 Data Engineer", [
        {"code": "F20", "cn": "ETL 适配器", "en": "ETL Adapters",
         "icon": "celery", "tech": "Celery · Airflow",
         "role": "9 个广告 / CRM / 归因平台",
         "in":  "OAuth 凭证、起止日期",
         "out": "raw_{platform} 仓库表",
         "api": "POST /etl/run · /etl/jobs/{id}",
         "subs": [
             "9 平台连接（GA4 · Meta · HubSpot · DV360）",
             "（StackAdapt · LeadRX · LiveRamp · Quorum · TikTok）",
             "OAuth 凭证加密存储（Fernet）",
             "增量同步（cursor / state 表）",
             "Mock 模式（dev 合成数据）",
             "失败重试（指数退避）",
             "同步状态追踪（成功/失败/部分）",
             "DAG 编排（Airflow scheduler）",
         ]},
        {"code": "F15", "cn": "字段映射", "en": "Field Mapping",
         "icon": "map", "tech": "dbt · SQL",
         "role": "原始字段 → Canonical → 业务实体",
         "in":  "raw_* 表 + Mapping 规则",
         "out": "Canonical schema 业务表",
         "api": "POST /mappings · /mappings/preview",
         "subs": [
             "Canonical Schema（统一字段集）",
             "4 种 Transform（direct / hash / lower / concat）",
             "实时预览（前 50 行变换结果）",
             "版本管理（每次保存生成版本）",
             "映射模板复用（按平台克隆）",
             "字段血缘追溯（lineage view）",
             "dbt staging → canonical → marts",
         ]},
        {"code": "C", "cn": "合规处理", "en": "Compliance Layer",
         "icon": "compliance", "tech": "Fernet · SHA-256",
         "role": "PHI Detector + 匿名化 + IP 截断",
         "in":  "raw record（含 PII/PHI 可能）",
         "out": "匿名化记录 + 告警日志",
         "api": "internal: phi_detector · anonymizer",
         "subs": [
             "PHI Detector（HIPAA 18 类标识符扫描）",
             "SHA-256 + Agency salt 哈希",
             "IP 截断（IPv4 /24 · IPv6 /48）",
             "邮箱 / 电话 / 姓名匿名化",
             "禁止 raw_json 字段（防绕过）",
             "审计日志写入（INSERT-only）",
             "告警通知（PHI 命中即发送）",
         ]},
     ]),

    (3, "AI Analytics", "AI 智能分析", "3 Agents · AI Brain",
     "人群画像 · 创意优化 · 跨渠道归因",
     "🤖 AI Agent · 👤 Marketing Analyst", [
        {"code": "F10", "cn": "人群画像 Agent", "en": "Persona Agent",
         "icon": "personas", "tech": "LLM · pgvector",
         "role": "受众分群 + 画像生成",
         "in":  "Canonical 数据 + 业务目标",
         "out": "Persona 画像 + 受众段",
         "api": "POST /personas/generate",
         "subs": [
             "受众分群算法（K-Means + 业务规则）",
             "LLM 画像描述生成（人格化文案）",
             "pgvector 向量检索（相似 Persona）",
             "Persona 标签库（行为 · 兴趣 · 渠道）",
             "A/B Persona 对比",
             "导出受众段（→ F21）",
             "历史版本快照",
         ]},
        {"code": "F11", "cn": "创意 Agent", "en": "Creative Agent",
         "icon": "creatives", "tech": "LLM · Brand",
         "role": "广告创意优化建议",
         "in":  "Brand 基调 + 历史 CTR",
         "out": "Creative 候选 + 评分",
         "api": "POST /creatives/recommend",
         "subs": [
             "创意文案生成（多 variant）",
             "标题 / 描述 / CTA 三段输出",
             "CTR 历史评分（参考过往表现）",
             "品牌调性约束（Brand voice）",
             "A/B 实验设计建议",
             "创意素材库管理",
             "多语言 / 多市场支持",
         ]},
        {"code": "F12", "cn": "归因 Agent", "en": "Attribution Agent",
         "icon": "attribution", "tech": "LLM · MTA",
         "role": "跨渠道归因模型",
         "in":  "Touchpoints + 转化事件",
         "out": "归因权重 + 渠道贡献",
         "api": "POST /attribution/run",
         "subs": [
             "多触点归因 (MTA) 模型",
             "First / Last / Linear / Time-decay",
             "跨渠道权重计算",
             "增量归因（incremental）",
             "渠道 ROI 排名",
             "归因报告（PDF / JSON）",
             "LLM 解读（归因结论自动总结）",
         ]},
        {"code": "P1", "cn": "AI 中枢", "en": "AI Brain · Warehouse",
         "icon": "brain", "tech": "OpenRouter · httpx",
         "role": "Token 预算 + 模型路由 + 审计",
         "in":  "Agent 调用请求",
         "out": "LLM 响应 + 用量记录",
         "api": "internal: brain.invoke()",
         "subs": [
             "模型路由（Claude / Gemini per agent）",
             "Token 预算控制（monthly_token_budget）",
             "用量记录（token_usage 表）",
             "预算耗尽 → 429 拦截",
             "Mock 模式（API key 为空时）",
             "Langfuse 追踪（trace + score）",
             "错误重试 + fallback 模型",
         ]},
     ]),

    (4, "Activation", "营销执行", "Campaigns · Audience Export",
     "活动管理 + 受众导出投放",
     "👤 Campaign Manager · 🤖 Worker", [
        {"code": "F19", "cn": "活动管理", "en": "Campaigns",
         "icon": "googleads", "tech": "FastAPI · Celery",
         "role": "跨平台活动视图 + 预算告警",
         "in":  "Campaign 配置 + 预算阈值",
         "out": "活动状态 + 预算告警邮件",
         "api": "POST /campaigns · /campaigns/budget",
         "subs": [
             "跨平台活动统一视图",
             "预算配置（日 / 月 / 总预算）",
             "实际花费 vs 预算 Pacing",
             "阈值告警（80% / 95% / 100%）",
             "邮件通知（SMTP）",
             "历史趋势图（CTR · CPM · ROAS）",
             "活动暂停 / 恢复（API 联动）",
             "标签 / 分组管理",
         ]},
        {"code": "F21", "cn": "受众导出", "en": "Audience Export",
         "icon": "audience", "tech": "Meta · DV360 SDK",
         "role": "导出到 Meta / DV360 投放",
         "in":  "Persona 受众段",
         "out": "Custom Audience ID + 导出任务",
         "api": "POST /audiences/export",
         "subs": [
             "Meta Custom Audience 推送",
             "DV360 Audience 推送",
             "邮箱 / 手机 SHA-256 哈希",
             "异步导出 Job（Celery）",
             "导出状态查询（成功 / 失败 / 处理中）",
             "配额管理（每日上限）",
             "失败回退 + 重试",
         ]},
     ]),

    (5, "Client Delivery", "客户交付", "Portal · Reports · Realtime",
     "客户消费成果：门户 / PDF / 实时通知",
     "🏢 Client · 👥 Stakeholder", [
        {"code": "F16", "cn": "客户门户", "en": "Client Portal",
         "icon": "portal", "tech": "React · MUI",
         "role": "客户登录 + 仪表板",
         "in":  "Client 凭证（受限令牌）",
         "out": "仪表板视图 + 下载链接",
         "api": "GET /portal/dashboard · /portal/reports",
         "subs": [
             "客户登录（限定权限令牌）",
             "仪表板（KPI · 活动 · 报告）",
             "报告下载列表（PDF / Excel）",
             "历史归档查询",
             "通知中心（与 F17 联动）",
             "多品牌切换（Agency 多 Brand）",
             "深色 / 浅色主题",
             "Web 端响应式（PC + 平板）",
         ]},
        {"code": "F22", "cn": "PDF 报告", "en": "PDF Reports",
         "icon": "pdf_report", "tech": "WeasyPrint · Celery",
         "role": "模板渲染 + 异步生成 + 邮件",
         "in":  "报告模板 + 数据范围",
         "out": "PDF 文件 + MinIO/S3 URL",
         "api": "POST /reports · /reports/{id}/download",
         "subs": [
             "报告模板库（季度 / 月度 / 周度）",
             "WeasyPrint HTML → PDF 渲染",
             "Celery 异步生成（避免阻塞）",
             "MinIO（dev）/ S3（prod）存储",
             "邮件投递（SMTP + 附件 / 下载链接）",
             "下载链接签名（限时 URL）",
             "PDF 加密（可选 · 客户密码）",
             "报告水印（Brand Logo）",
         ]},
        {"code": "F17", "cn": "实时通知", "en": "Realtime Notifications",
         "icon": "ws", "tech": "WebSocket · Redis",
         "role": "WebSocket /ws 推送 + 历史",
         "in":  "系统事件（导入完成 · 预算告警）",
         "out": "实时推送 + 历史通知列表",
         "api": "WS /ws · GET /notifications",
         "subs": [
             "WebSocket /ws 长连接",
             "事件类型分类（导入 · 告警 · 报告完成）",
             "已读 / 未读状态管理",
             "历史回放（重连补推）",
             "Redis Pub/Sub 中转",
             "桌面通知（浏览器 Notification API）",
             "邮件 Fallback（重要事件）",
         ]},
     ]),

    (6, "Governance", "平台治理", "Observability · Compliance · Audit",
     "持续合规 · 全链路可观测 · 审计追溯",
     "👤 Admin · 🛡 Compliance Officer", [
        {"code": "F18", "cn": "可观测性", "en": "Observability",
         "icon": "langfuse", "tech": "Langfuse · Sentry",
         "role": "LLM 追踪 + 错误监控 + 健康检查",
         "in":  "应用日志 / LLM 调用 / 错误事件",
         "out": "Trace · Issue · 健康指标",
         "api": "GET /health · /metrics",
         "subs": [
             "Langfuse LLM trace（每次调用一条 trace）",
             "Sentry 错误聚合 + 通知",
             "/health 健康检查（DB · Redis · LLM）",
             "/metrics Prometheus 格式",
             "慢查询追踪（>200ms 自动记录）",
             "自定义业务指标（活跃用户 · 任务量）",
             "审计日志（操作 + 资源 + 时间）",
         ]},
        {"code": "C+", "cn": "合规治理", "en": "Compliance · DSAR",
         "icon": "compliance", "tech": "Fernet · Audit-Only",
         "role": "GDPR / CCPA / HIPAA + DSAR + 保留",
         "in":  "DSAR 请求 / 保留策略 / 违规事件",
         "out": "导出/删除/通知 + 审计日志",
         "api": "POST /dsar · GET /audit/logs",
         "subs": [
             "DSAR 受理（access · delete · export · rectify）",
             "DSAR SLA（GDPR 30d / CCPA 45d / HIPAA 30d）",
             "数据保留策略（最严：审计 6 年）",
             "审计日志（6 年 INSERT-only · 不可改）",
             "违规通知（GDPR 72h / HIPAA 60d）",
             "BAA 协议状态 + 到期提醒",
             "加密密钥轮换（Agency 独立密钥）",
             "数据最小化策略",
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

    # 层间数据流箭头（band gap 中心，水平居中偏右）
    flow_x = W // 2 + 280
    flow_defs = [
        (1, "客户启动",       "Brand · 历史数据 · 凭证",    LAYER_COLORS[1]),
        (2, "原始数据已入仓", "raw_* · Canonical · 匿名化", EDGE_DATA),
        (3, "AI 洞察就绪",    "Persona · 创意 · 归因",       EDGE_AI),
        (4, "投放执行完成",   "活动状态 · 受众导出 ID",      LAYER_COLORS[4]),
        (5, "客户消费成果",   "门户 · PDF · 实时推送",       LAYER_COLORS[5]),
    ]
    for (lf, top, bot, col) in flow_defs:
        parts.append(flow_arrow(flow_x, lf, top, bot, col))

    # 合规反馈环：走 layer_label 与 band 之间的左侧通道（不穿过卡片）
    gov_x = PAD + LAYER_LABEL_W + 10
    y_l6_top = band_y(6) - 4
    y_l2_top = band_y(2) + 8
    parts.append(
        f'<path d="M {gov_x} {y_l6_top} L {gov_x} {y_l2_top}"'
        f' stroke="{EDGE_GUARD}" stroke-width="1.8" fill="none" stroke-dasharray="7 5"'
        f' opacity="0.75" marker-end="url(#arrow-{EDGE_GUARD[1:]})"/>'
    )
    # 标题放在 L5→L6 band gap（足够空间，避开所有卡片）
    label_y = band_y(6) - BAND_GAP // 2
    parts.append(
        f'<rect x="{gov_x - 86}" y="{label_y - 18}" width="172" height="36"'
        f' fill="{BG}" stroke="{EDGE_GUARD}" stroke-width="1.4" rx="9"/>'
        f'<text x="{gov_x}" y="{label_y - 2}" font-family="Helvetica" font-size="12"'
        f' font-weight="700" fill="{EDGE_GUARD}"'
        f' text-anchor="middle">↺ 合规反馈环</text>'
        f'<text x="{gov_x}" y="{label_y + 12}" font-family="Helvetica" font-size="9"'
        f' fill="{DIM_LABEL}" text-anchor="middle">DSAR · 保留 · 违规通知</text>'
    )

    parts.append(footer_panel())
    parts.append('</svg>')
    return "\n".join(parts)


def main() -> None:
    svg = build_svg()
    out_svg = ROOT / "business-flow-layered.svg"
    out_svg.write_text(svg)
    print(f"✓ wrote {out_svg.name} ({len(svg):,} bytes)")
    out_png = ROOT / "business-flow-layered.png"
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
