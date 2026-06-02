# p1-etl-warehouse-ai 需求文档

> 来源：ReceptivIQ 底层框架开发计划 Phase 1
> 状态：F-06 ~ F-09 ETL / 仓库 / AI 基础层聚合模块

## 功能概述

数据流通层 + AI 推理层。包含 ETL 数据管道、Canonical Schema + dbt 转换、Snowflake 数据仓库、Core AI Brain（LLM 路由器）4 个子模块。

## 功能需求

### FR-1: ETL 数据管道（F-06）

- BaseAdapter 抽象模式（fetch / get_raw_table / transform）
- ETLRunner 执行 extract → PHI 扫描 → 匿名化 → transform → 仓库写入 → sync 状态更新
- GA4 / Meta Ads / HubSpot 三个初始 adapter
- 支持 mock 模式（credentials.get("mock")）

### FR-2: Canonical Schema + dbt 转换（F-07）

- Staging 层：各平台原始数据标准化
- Canonical 层：跨平台统一事件 schema
- Marts 层：业务聚合（campaign / persona / attribution）
- dbt 版本控制 + 数据质量测试

### FR-3: Snowflake 数据仓库（F-08）

- 双后端：DuckDB（开发）/ Snowflake（生产）
- `WAREHOUSE_BACKEND` 环境变量切换
- SQL 注入防护：语句前缀白名单 + 表名列名正则
- ETL sync state 跟踪

### FR-4: Core AI Brain（F-09）

- LLM 路由器：根据 agent 类型选择模型
- OpenRouter 统一入口（Claude / GPT / Gemini）
- Token usage 追踪（per agency）
- 月度预算控制（429 错误当耗尽）
- Langfuse 可观测性

## 非功能需求

- ETL 数据延迟 ≤ 30 分钟
- AI 查询响应 < 5 秒（简单）/ < 15 秒（复杂）
- Token 成本估算（基于 OpenRouter 定价）

## 合规要求

- PII/PHI 不以明文入仓库（hash_identifier 哈希）
- ETL Runner 无条件匿名化
- 禁止 raw_json 字段（新 adapter）
- AI 查询记录审计日志
