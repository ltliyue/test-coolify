#!/usr/bin/env python3
"""ReceptivIQ Platform — 前端功能架构图 (Frontend Feature Map)

按用户使用路径分层组织所有前端页面与子组件：
  公共入口 → 工作台 → 数据 UI → AI 工作台 → 营销交付 → 客户门户 + 管理

每个模块标注：路由 · 用户 · 入口 · 主操作 · 关键 API · UI 子组件清单。
"""
from __future__ import annotations
import base64
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
ICONS = ROOT / "icons"

# 主题
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

# 前端版色板：偏屏幕/UI 调，与业务流程图区分
LAYER_COLORS = {
    1: "#0EA5E9",   # 公共入口 — sky
    2: "#6366F1",   # 工作台 — indigo
    3: "#14B8A6",   # 数据 UI — teal
    4: "#A855F7",   # AI 工作台 — purple
    5: "#F97316",   # 营销交付 — orange
    6: "#F43F5E",   # 客户门户 + 管理 — rose
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


# ── 模块卡片（含 UI 子组件清单）────────────────────────────────
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
    # 屏幕角标（窗口控制点装饰）
    for i, dot_color in enumerate(["#F87171", "#FBBF24", "#34D399"]):
        parts.append(
            f'<circle cx="{x + w - 18 - i * 12}" cy="{y + 16}" r="3.5"'
            f' fill="{dot_color}" opacity="0.7"/>'
        )

    # 顶部：route 徽章 + 名称 + role 角色
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

    # 子组件清单
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
        f' letter-spacing="1.4">▸ UI 子组件 / COMPONENTS</text>'
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


# ── 跨层带标签数据流箭头 ─────────────────────────────────────
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
    ReceptivIQ Platform — 前端功能架构图 (Frontend Feature Map)
  </text>
  <text x="{W // 2}" y="104" font-family="Helvetica" font-size="14"
        fill="{DIM_LABEL}" text-anchor="middle">
    User Journey · 6 层 · 21 页面/模块 · 每页详注路由/入口/操作/API + UI 子组件清单
  </text>
  <text x="{W // 2}" y="130" font-family="Helvetica" font-size="11"
        fill="{DIM_LABEL}" text-anchor="middle" font-style="italic">
    自上而下：公共入口 → 工作台 → 数据 UI → AI 工作台 → 营销交付 → 客户门户与管理
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
        ("21", "页面 / 模块 Pages"),
        ("6",  "用户旅程 Layers"),
        ("React 19", "+ TypeScript"),
        ("MUI v5", "组件库 UI Library"),
        ("Vite", "Dev Server + Build"),
        ("⌘K", "全局命令面板"),
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
        ("AI 触发",                 EDGE_AI),
        ("数据读取",                EDGE_DATA),
        ("👤 Agency / Brand",       LAYER_COLORS[2]),
        ("🏢 Client (受限)",        LAYER_COLORS[6]),
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


# ── 前端模块数据 ─────────────────────────────────────────────
LAYERS_DATA = [
    (1, "Public Entry", "公共入口", "Auth · Entry Pages",
     "未认证入口：登录 / 重置 / 客户门户登录",
     "🌐 公开访问 Public", [
        {"route": "/login", "cn": "登录页", "en": "Sign-in",
         "icon": "auth", "role": "邮箱登录 + Google OAuth",
         "entry": "未认证访问受限页面 → 重定向",
         "actions": "登录 → 跳转主页",
         "api": "POST /auth/login · /auth/google",
         "subs": [
             "邮箱 + 密码登录表单",
             "「Sign in with Google」 按钮",
             "密码强度提示",
             "失败次数提示（5 次后锁定）",
             "「记住我」复选框",
             "「忘记密码」链接",
             "错误消息内联展示",
         ]},
        {"route": "/reset-password", "cn": "密码重置", "en": "Reset Password",
         "icon": "smtp", "role": "忘记密码 / 邮件验证",
         "entry": "登录页「忘记密码」链接",
         "actions": "发送重置邮件 / 设置新密码",
         "api": "POST /auth/forgot · /auth/reset",
         "subs": [
             "输入邮箱发送重置链接",
             "邮件链接含一次性 token",
             "新密码 + 确认密码字段",
             "密码强度实时检查",
             "重置成功提示 + 跳转",
             "Token 失效错误处理",
         ]},
        {"route": "/client/login", "cn": "客户门户登录", "en": "Client Portal Login",
         "icon": "portal", "role": "客户独立登录入口",
         "entry": "客户邮件中的门户链接",
         "actions": "登录 → 客户仪表板",
         "api": "POST /portal/auth/login",
         "subs": [
             "独立登录页（Brand Logo）",
             "邮箱 + 一次性 PIN 登录",
             "多 Brand 选择（如有）",
             "隐私声明 + Cookie 提示",
             "「← 返回 ReceptivIQ」 链接",
             "限时令牌（24h 过期）",
         ]},
     ]),

    (2, "Workspace", "工作台", "Dashboard · Nav · Search",
     "主工作区：首页 + 全局导航 + 命令面板",
     "👤 Agency Admin · Brand Manager", [
        {"route": "/", "cn": "主仪表板", "en": "Home Dashboard",
         "icon": "dashboard", "role": "KPI 概览 / 快捷入口",
         "entry": "登录成功后默认页",
         "actions": "查看 KPI / 跳转业务页",
         "api": "GET /dashboard · /campaigns/summary",
         "subs": [
             "KPI 卡片（活动 · 受众 · 报告 · 预算）",
             "最近活动时间线（时间倒序）",
             "待办任务面板（onboarding · 审批）",
             "快捷操作按钮（新建活动 / 导入数据）",
             "数据更新时间戳",
             "多 Brand 切换器",
             "今日预算消耗概览",
         ]},
        {"route": "<Sidebar/>", "cn": "全局导航", "en": "Global Navigation",
         "icon": "react", "role": "侧边栏 + 顶栏 + 切换器",
         "entry": "所有受认证页面",
         "actions": "切换 Brand / 页面 / 主题",
         "api": "GET /me · /brands/me",
         "subs": [
             "侧边栏（可折叠 + 多级菜单）",
             "顶栏（搜索 + 通知 + 头像）",
             "Brand 切换器（Agency 多品牌）",
             "主题切换（深色 / 浅色）",
             "通知 Badge（红点 + 数字）",
             "用户菜单（设置 / 退出）",
             "面包屑 Breadcrumb",
         ]},
        {"route": "⌘K", "cn": "命令面板", "en": "Command Palette",
         "icon": "vite", "role": "全局快捷搜索",
         "entry": "⌘K / Ctrl+K 快捷键",
         "actions": "搜索实体 / 触发动作",
         "api": "GET /search?q=",
         "subs": [
             "⌘K 唤起命令面板",
             "搜索类型：Brand / Campaign / Persona / Report",
             "模糊匹配 + 关键词高亮",
             "最近访问历史",
             "快捷动作（「新建活动」「导入」等）",
             "键盘导航 (↑↓ Enter Esc)",
         ]},
     ]),

    (3, "Data UI", "数据接入 UI", "Brand · Import · ETL · Mapping",
     "数据接入页面：入驻看板 / 导入向导 / 连接管理 / 映射编辑器",
     "👤 Data Engineer · Brand Manager", [
        {"route": "/brands/:id", "cn": "品牌入驻看板", "en": "Brand Onboarding Board",
         "icon": "client", "role": "Trello 风格拖拽看板",
         "entry": "新 Brand 创建后自动跳转",
         "actions": "拖拽任务 / 审批 / 完成入驻",
         "api": "GET /brands/:id · POST /brands/:id/tasks",
         "subs": [
             "Trello 看板（待办 / 进行中 / 完成）",
             "拖拽换列（react-dnd）",
             "任务详情侧抽屉",
             "责任人 + 截止日期",
             "审批按钮（提交 → 通过）",
             "进度百分比顶部进度条",
             "BAA 协议上传区（HIPAA）",
             "品牌素材库（Logo / 调色板）",
         ]},
        {"route": "/imports/new", "cn": "历史导入向导", "en": "Import Wizard",
         "icon": "apacheairflow", "role": "3 步导入：上传 / 映射 / 验证",
         "entry": "主页快捷操作 / 数据菜单",
         "actions": "导入数据 → 写入仓库",
         "api": "POST /imports · /imports/{id}/validate",
         "subs": [
             "步骤 1：上传 CSV / Excel（≤100MB）",
             "步骤 2：字段映射 + 智能匹配",
             "步骤 3：Dry-run 预览（前 100 行）",
             "文件类型 + 大小校验",
             "进度条 + WebSocket 实时反馈",
             "失败行表格（行号 + 错误码）",
             "回滚按钮（导入失败后）",
             "导入历史版本对比",
         ]},
        {"route": "/etl/connections", "cn": "ETL 连接管理", "en": "ETL Connections",
         "icon": "celery", "role": "9 平台 OAuth 授权",
         "entry": "数据菜单 / 设置",
         "actions": "授权 / 触发同步 / 查看日志",
         "api": "GET /etl/connections · POST /etl/run",
         "subs": [
             "9 平台卡片（GA4 / Meta / HubSpot / DV360 …）",
             "OAuth「连接」按钮",
             "凭证状态指示（有效 / 即将过期）",
             "上次同步时间 + 状态",
             "手动触发同步按钮",
             "同步历史日志面板",
             "失败重试 + 错误详情",
         ]},
        {"route": "/mappings/:id", "cn": "字段映射编辑器", "en": "Field Mapping Editor",
         "icon": "map", "role": "拖拽映射 + Transform + 预览",
         "entry": "数据菜单 / ETL 同步完成提示",
         "actions": "保存映射 / 应用版本",
         "api": "POST /mappings · /mappings/preview",
         "subs": [
             "左侧：原始字段列表",
             "右侧：Canonical Schema",
             "拖拽连接 + 高亮匹配",
             "Transform 下拉（direct/hash/lower/concat）",
             "实时预览（前 50 行变换结果）",
             "版本下拉切换",
             "保存 + 应用按钮",
             "字段血缘可视化",
         ]},
     ]),

    (4, "AI Workspace", "AI 工作台", "Persona · Creative · Attribution · Settings",
     "AI 三 Agent 工作台 + 模型设置",
     "👤 Marketing Analyst · 🤖 AI", [
        {"route": "/personas", "cn": "Persona 库", "en": "Persona Library",
         "icon": "personas", "role": "列表 + 生成 + 详情",
         "entry": "AI 菜单 / 主页 KPI 跳转",
         "actions": "创建 / 编辑 / 导出受众",
         "api": "GET /personas · POST /personas/generate",
         "subs": [
             "Persona 卡片网格 + 标签过滤",
             "创建向导（业务目标 + 数据范围）",
             "生成中加载动画（流式输出）",
             "Persona 详情面板（属性 + 描述）",
             "A/B 对比双栏视图",
             "「导出到 Meta / DV360」按钮",
             "历史版本快照",
             "pgvector 相似 Persona 推荐",
         ]},
        {"route": "/creatives", "cn": "创意推荐", "en": "Creative Browser",
         "icon": "creatives", "role": "广告创意候选浏览",
         "entry": "AI 菜单 / 活动详情",
         "actions": "选用创意 / 创建 A/B 实验",
         "api": "GET /creatives · POST /creatives/recommend",
         "subs": [
             "创意候选网格（图 + 文案）",
             "CTR 评分排序",
             "标题 / 描述 / CTA 三段展示",
             "品牌调性 chip",
             "「新建 A/B 实验」按钮",
             "多语言切换",
             "历史 variant 对比表",
         ]},
        {"route": "/attribution", "cn": "归因分析", "en": "Attribution Analytics",
         "icon": "attribution", "role": "跨渠道归因可视化",
         "entry": "AI 菜单 / 活动详情",
         "actions": "选模型 / 导出报告",
         "api": "POST /attribution/run",
         "subs": [
             "模型选择（First/Last/Linear/Time-decay/MTA）",
             "触点时间线视图",
             "渠道贡献饼图",
             "渠道 ROI 排名表",
             "LLM 解读段落（自动总结）",
             "「导出 PDF」按钮",
             "增量归因模式切换",
         ]},
        {"route": "/settings/ai", "cn": "AI 模型设置", "en": "AI Settings",
         "icon": "brain", "role": "模型路由 + 预算",
         "entry": "设置菜单",
         "actions": "切模型 / 调预算",
         "api": "GET/POST /settings/ai",
         "subs": [
             "三 Agent 模型路由下拉",
             "Claude / Gemini 模型选项",
             "月度 Token 预算输入",
             "当前用量进度条",
             "预算告警阈值（80% / 95%）",
             "Mock 模式开关（dev）",
             "Langfuse Trace 跳转链接",
         ]},
     ]),

    (5, "Activation · Delivery", "营销与交付", "Campaign · Audience · Report",
     "活动管理 + 受众导出 + PDF 报告",
     "👤 Campaign Manager", [
        {"route": "/campaigns", "cn": "活动管理", "en": "Campaigns",
         "icon": "googleads", "role": "跨平台活动 + 预算",
         "entry": "主页 / 营销菜单",
         "actions": "创建 / 暂停 / 调预算",
         "api": "GET/POST /campaigns · /campaigns/budget",
         "subs": [
             "活动列表（DataGrid 排序 / 筛选）",
             "多平台聚合视图（GA4 / Meta / DV360）",
             "活动详情侧抽屉",
             "预算配置（日 / 月 / 总）",
             "Pacing 折线图（花费 vs 预算）",
             "阈值告警设置（80 / 95 / 100%）",
             "暂停 / 恢复 按钮（API 联动）",
             "标签 + 分组管理",
         ]},
        {"route": "/audiences/export", "cn": "受众导出", "en": "Audience Export",
         "icon": "audience", "role": "Meta / DV360 受众投放",
         "entry": "Persona 详情 / 受众菜单",
         "actions": "推送受众 / 查任务状态",
         "api": "POST /audiences/export",
         "subs": [
             "选 Persona 受众段",
             "平台选择（Meta CA / DV360 Aud.）",
             "哈希预览（邮箱 → SHA-256）",
             "异步任务进度条",
             "导出历史列表（成功 / 失败 / 进行中）",
             "失败重试按钮",
             "配额余量显示",
         ]},
        {"route": "/reports", "cn": "PDF 报告", "en": "PDF Reports",
         "icon": "pdf_report", "role": "模板渲染 + 异步生成",
         "entry": "主页 / 报告菜单",
         "actions": "选模板 / 生成 / 投递",
         "api": "POST /reports · GET /reports/{id}/download",
         "subs": [
             "模板库（季 / 月 / 周 / 自定义）",
             "数据范围选择器（日期 / Brand / 活动）",
             "实时 HTML 预览",
             "「生成 PDF」按钮（异步 + 队列）",
             "任务队列状态",
             "签名下载链接（限时）",
             "「发送邮件给客户」按钮",
             "报告水印（Brand Logo）",
         ]},
     ]),

    (6, "Client · Admin", "客户门户与管理", "Portal · Users · Compliance · Health",
     "客户独立门户 + 后台管理 + 合规 + 监控",
     "🏢 Client · 👤 Admin · 🛡 Officer", [
        {"route": "/client/*", "cn": "客户门户", "en": "Client Portal",
         "icon": "portal", "role": "客户独立视图（限权）",
         "entry": "客户邮件链接",
         "actions": "查看 KPI / 下载报告 / 收通知",
         "api": "GET /portal/dashboard · /portal/reports",
         "subs": [
             "Brand 风格化品牌色 + Logo",
             "限权仪表板（仅查看）",
             "活动概览（KPI）",
             "报告下载列表（签名 URL）",
             "通知中心（WebSocket 推送）",
             "多 Brand 切换（若有）",
             "深色 / 浅色主题",
             "隐私 / Cookie 设置",
         ]},
        {"route": "/settings/users", "cn": "用户管理", "en": "User Management",
         "icon": "staff", "role": "Agency 用户 + 角色",
         "entry": "设置菜单",
         "actions": "邀请 / 改角色 / 禁用",
         "api": "GET/POST /users · /roles",
         "subs": [
             "用户列表（DataGrid）",
             "邀请用户（邮箱 + 角色）",
             "角色管理（预定义 + 自定义）",
             "权限矩阵视图",
             "禁用 / 启用切换",
             "最后登录时间显示",
             "强制登出按钮",
         ]},
        {"route": "/compliance", "cn": "合规中心", "en": "Compliance Center",
         "icon": "compliance", "role": "DSAR + 审计日志",
         "entry": "设置菜单 / 合规告警",
         "actions": "受理 DSAR / 查审计",
         "api": "POST /dsar · GET /audit/logs",
         "subs": [
             "DSAR 请求列表（access · delete · export · rectify）",
             "SLA 倒计时（30d / 45d）",
             "审计日志查询（用户 / 资源 / 时间）",
             "6 年归档查看",
             "BAA 协议状态卡片",
             "数据保留策略配置",
             "违规事件登记表",
         ]},
        {"route": "/admin/health", "cn": "系统监控", "en": "System Health",
         "icon": "langfuse", "role": "服务状态 + 指标",
         "entry": "设置菜单 / 顶栏状态点",
         "actions": "看状态 / 跳告警",
         "api": "GET /health · /metrics",
         "subs": [
             "服务状态卡片（DB · Redis · LLM）",
             "健康指标实时图",
             "慢查询列表",
             "Langfuse trace 跳转",
             "Sentry issue 列表",
             "系统资源使用率",
             "手动告警测试按钮",
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

    # 层间用户旅程箭头
    flow_x = W // 2 + 280
    flow_defs = [
        (1, "登录成功",     "JWT · Session 建立",         LAYER_COLORS[1]),
        (2, "选业务入口",   "Brand · Campaign · Persona", EDGE_USER),
        (3, "数据准备就绪", "raw_* 已入仓 · 映射已配置",   EDGE_DATA),
        (4, "AI 产出洞察",  "Persona · 创意 · 归因",       EDGE_AI),
        (5, "执行结果产出", "活动状态 · 报告 · 受众 ID",   LAYER_COLORS[5]),
    ]
    for (lf, top, bot, col) in flow_defs:
        parts.append(flow_arrow(flow_x, lf, top, bot, col))

    # 客户门户回路：从 L6 客户门户 引回 L5（虚线）
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
        f' text-anchor="middle">↺ 客户消费回路</text>'
        f'<text x="{cp_x}" y="{label_y + 12}" font-family="Helvetica" font-size="9"'
        f' fill="{DIM_LABEL}" text-anchor="middle">查看报告 · 收通知 · 反馈</text>'
    )

    parts.append(footer_panel())
    parts.append('</svg>')
    return "\n".join(parts)


def main() -> None:
    svg = build_svg()
    out_svg = ROOT / "frontend-feature-layered.svg"
    out_svg.write_text(svg)
    print(f"✓ wrote {out_svg.name} ({len(svg):,} bytes)")
    out_png = ROOT / "frontend-feature-layered.png"
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
