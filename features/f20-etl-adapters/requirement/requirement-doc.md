# f20-etl-adapters 需求文档

> 来源：ReceptivIQ Dev Brief v2 §4B — ETL Pipeline & Data Ingestion
> 状态：MVP P1 (Quorum/LeadRX/LiveRamp) + P2 (DV360/StackAdapt)

## 功能概述

补齐缺失的 ETL 数据适配器，使 ReceptivIQ 能从更多外部平台拉取数据到数据仓库。当前已有 GA4、Meta Ads、HubSpot 三个 adapter。

## MVP P1 适配器

### FR-1: Quorum Adapter

- 平台类型：Audience（行为数据）
- 同步频率：Daily
- 数据内容：政治/倡导活动数据、受众行为信号
- 认证方式：API Key

### FR-2: LeadRX Adapter

- 平台类型：Attribution（归因数据）
- 同步频率：1 小时
- 数据内容：lead 归因、转化路径、touchpoint 数据
- 认证方式：API Key

### FR-3: LiveRamp Adapter

- 平台类型：Identity（身份解析）
- 同步频率：Daily
- 数据内容：跨设备身份匹配、audience segment 数据
- 认证方式：API Key
- 注意：需确认合同状态（Dev Brief 标注 confirm contract）

## MVP P2 适配器（优先级次之）

### FR-4: DV360 Adapter

- 同步频率：1 小时
- 数据内容：programmatic campaign 数据（impressions/clicks/spend/conversions）

### FR-5: StackAdapt Adapter

- 同步频率：1 小时
- 数据内容：native/programmatic ad 数据

## 技术约束

- 必须继承 `BaseAdapter` 基类（fetch + get_raw_table + transform）
- 输出写入 `raw_<platform>` 表
- 支持 mock 数据模式用于开发测试
- 遵循 PII/PHI 合规层（数据入仓前经 anonymizer 处理）
- 需在 dbt staging 层新增对应 `stg_<platform>.sql`
