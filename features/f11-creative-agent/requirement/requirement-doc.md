# f11-creative-agent 需求文档

> 来源：Dev Brief v2 §Pillar 2 — Creative & Content Engine
> 状态：MVP P2

## 功能概述

基于 persona + 品牌配置生成多平台创意文案和图片资产。支持四平台（Meta / DV360 / TikTok / Google Ads）的格式规范。

## 功能需求

### FR-1: 多平台创意生成

- 输入：persona_id / brand_config / 目标平台
- 输出：Generation 主记录 + N 个 GenerationResult（每个平台一个）
- 支持四平台：Meta Ads / DV360 / TikTok Ads / Google Ads
- 每个结果含 headline / body / cta / image_prompt

### FR-2: Persona 上下文注入

- 读取 persona 的 psychographics + recommended_tone
- 注入 Creative Agent 的 system prompt
- 确保文案与 persona 匹配

### FR-3: 品牌合规过滤

- 规则式：禁用词、颜色一致性、字体限制
- AI 语调评分（Phase 2）

### FR-4: 创意 CRUD

- 列出 generation / 详情 / 删除
- 按 client_id / agent_type 过滤

## 非功能需求

- 生成延迟：Claude Sonnet 约 8-15 秒
- 支持 mock 模式开发测试

## 合规要求

- 所有 API 端点带 audit_simple()
- Token usage 按 agent 类型分别追踪
- 生成结果含 agency_id 隔离
