# f12-attribution-agent 需求文档

> 来源：Dev Brief v2 §Pillar 3 — Attribution & Measurement
> 状态：MVP P3 (partial)

## 功能概述

多触点归因分析。基于 LeadRX + GA4 + LiveRamp 数据生成归因报告，输出渠道贡献度、成本效率、跨渠道路径分析。

## 功能需求

### FR-1: 归因报告生成

- 输入：date_from / date_to / client_id（可选）
- 查询仓库 canonical_events + attribution 数据
- 调用 Attribution Agent（Claude Sonnet）
- 输出 AttributionReport：channels / results JSONB

### FR-2: 多触点模型

- Last-touch / First-touch / Linear / Time-decay
- 归因权重计算
- 跨渠道路径分析

### FR-3: AI 洞察

- 自动生成 insights 段落（plain English 摘要）
- 适用于客户面向的 Client View

### FR-4: 报告 CRUD

- 列出历史报告 / 详情 / 按日期范围过滤
- 按 agency_id 隔离

## 非功能需求

- 报告生成延迟 < 2 分钟
- 支持 mock 模式

## 合规要求

- 所有 API 端点带 audit_simple()
- 查询 conversion_id 为哈希值（LeadRX adapter 已处理）
- 仓库只读查询需参数化 SQL
