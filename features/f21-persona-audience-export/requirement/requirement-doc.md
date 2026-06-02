# f21-persona-audience-export 需求文档

> 来源：Dev Brief v2 §Pillar 1 (Persona-to-Audience Export) + §Pillar 4 (共享)
> 状态：MVP — 手动触发导出，Phase 2 自动化

## 功能概述

将 ReceptivIQ 生成的 Persona 对象（结构化受众画像）导出为广告平台的受众定向配置，实现**研究 → 媒介投放**的闭环集成。MVP 支持 Meta Ads 和 DV360 两个平台。

## MVP 功能需求

### FR-1: Persona → Meta Ads Custom Audience

- 读取 Persona 对象的 psychographics + channel_preferences
- 转换为 Meta Ads Marketing API 的 Custom Audience targeting spec
- 通过 Meta API 创建 Custom Audience
- 记录导出状态（成功/失败/external_audience_id）

### FR-2: Persona → DV360 Audience Segment

- 读取 Persona 对象转换为 DV360 audience targeting spec
- 通过 DV360 API 创建 Audience Segment
- 记录导出状态

### FR-3: 导出历史记录

- 跟踪每次导出的状态、目标平台、external ID
- 支持查看导出历史
- 支持重新导出（覆盖或创建新受众）

### FR-4: 导出前预览

- 在实际调用平台 API 之前展示转换后的 targeting spec
- 用户确认后执行导出

## 非功能需求

- 导出操作异步执行（Celery task），避免 API 超时
- 导出失败自动重试 1 次
- 租户隔离：只能导出本 agency 的 persona

## 合规要求

- 导出操作必须有审计日志（含 persona_id、目标平台、导出结果）
- persona 的 psychographics 中如含 PII 字段，导出前必须过滤
- 不得将用户 email/phone 等 Level 2+ 数据直接传递给广告平台（仅传 targeting 属性）
- 所有平台 API 凭证从 Credential Vault 解密获取

## Out of MVP Scope

- 自动触发导出（Phase 2 Media Buying Agent）
- 导出到 StackAdapt / TikTok（Phase 2）
- 受众同步（双向：平台 → ReceptivIQ）
