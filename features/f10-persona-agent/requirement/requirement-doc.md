# f10-persona-agent 需求文档

> 来源：Dev Brief v2 §Pillar 1 — Market Research Intelligence
> 状态：MVP P1

## 功能概述

生成结构化 Persona 对象（受众画像），作为 Pillar 2（创意）、Pillar 3（归因）、Pillar 4（媒介投放）的输入。Persona 不是静态 PDF，而是系统可引用和操作的一等数据实体。

## 功能需求

### FR-1: Persona CRUD

- 手动创建 / 读取 / 更新 / 软删除（is_active=false）
- 按 source 过滤（manual / ai）
- 租户隔离（agency_id NOT NULL）

### FR-2: AI 自动生成 Persona

- 输入：prompt + client 品牌配置 + 可选 client_id
- 调用 Claude Opus（PERSONA_MODEL 环境变量配置）
- 输出：3-7 个命名画像，含 psychographics、channel_preferences、recommended_tone
- Token 预算检查（预算耗尽返回 429）
- Mock 模式（OPENROUTER_API_KEY 为空时）

### FR-3: 结构化 Audience Blueprint

- psychographics JSON：心理/行为特征
- channel_preferences JSON：渠道偏好
- recommended_tone：推荐语调
- 必须是一等数据实体（不是文本报告）

### FR-4: 多数据源输入

- GA4 行为数据
- Quorum 受众数据
- HubSpot CRM 数据
- 社交 API 信号

## 非功能需求

- 生成延迟：Claude Opus 约 15-30 秒
- 首次生成无历史数据时，UX 需展示置信度提示

## 合规要求

- 所有 API 端点带 audit_simple()
- psychographics 字段禁止存储 PII（email / phone / name）
- agency_id 强制隔离（L-01 合规修复）
