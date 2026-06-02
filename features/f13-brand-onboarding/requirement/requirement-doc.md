# f13-brand-onboarding 需求文档

> 来源：Dev Brief v2 §4D — Brand Onboarding System
> 状态：MVP 内部工具，Phase 2 客户自服务

## 功能概述

品牌配置入驻系统。brand_config 是所有 Pillar agent 的共享上下文（颜色、字体、语调、禁用词），直接影响创意生成、报告模板、客户门户主题。

## 功能需求

### FR-1: brand_config 存储

- Agency 级 + Client 级双层
- JSONB 字段存储结构化配置
- 包含：colors / fonts / tone / logo_url / voice / regulatory_flags / prohibited_terms

### FR-2: GET / PUT / DELETE API

- GET 返回当前配置（空时返回默认模板）
- PUT 使用 PATCH 语义（合并更新，不是全量替换）
- DELETE 重置为空

### FR-3: PATCH 合并语义

- 深度合并（nested dict 递归）
- 单字段更新不影响其他字段
- 版本追踪（updated_at）

### FR-4: 多组件消费

- Creative Agent：注入 prompt
- Report Engine：PDF 主题色
- Client Portal：白标主题

## 非功能需求

- brand_config 大小限制 4KB（防止滥用）

## 合规要求

- 所有 API 端点带 audit_simple()
- agency_id 隔离
- 不存储用户 PII

## Phase 2 后续

- PDF / 图片品牌手册上传 + AI 解析（自动提取色彩/字体/语调）
- 客户自服务入驻流程
