# f14-historical-import 需求文档

> 来源：Dev Brief v2 §3C — Historical Data & LLM Seeding
> 状态：MVP 内部工具

## 功能概述

手动历史数据导入，用于 AI 冷启动阶段提供初始数据基础。Rose 明确要求："historical campaign data can be manually ingested to seed the AI layer"。

## 功能需求

### FR-1: CSV 上传端点

- POST `/imports` 接受 CSV 文件 + platform 参数
- 验证文件非空、格式有效
- 返回 import job 状态

### FR-2: 三平台自动检测

- GA4 / Meta Ads / HubSpot 三种 CSV 格式
- 基于表头字段自动识别平台（无需显式参数）
- 无法识别时返回 422

### FR-3: 规范化 + 入仓

- CSV 解析 → 字段映射到 canonical schema
- 经过 PHI 扫描 + 匿名化（复用 ETL Runner 合规层）
- 写入 DuckDB / Snowflake raw 表

### FR-4: 导入历史追踪

- import job 状态：pending / success / failed
- 记录 records_imported / errors

## 非功能需求

- 单次文件 ≤ 50MB
- 12 个月历史数据估算（per integration source）

## 合规要求

- 导入前 PHI 扫描拦截
- 用户标识符哈希（与实时 ETL 一致）
- 文件不持久化（处理后删除）
- 审计日志记录 import action
