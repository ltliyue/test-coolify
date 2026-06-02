# f20-etl-adapters 用户测试文档

> 版本：v1.0 | 日期：2026-04-02

## 测试环境

- Backend: pytest + DuckDB (warehouse mock)
- Mock 模式: credentials={"mock": True}
- 前置数据: agency + integration 已创建

---

## TC-01: Quorum Adapter — Mock 数据拉取

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 创建 QuorumAdapter(credentials={"mock":True}, agency_id) | 实例化成功 |
| 2 | 调用 fetch("2026-03-01", "2026-03-31") | 返回 (records, None)，records 非空 |
| 3 | 检查 records[0] 字段 | 含 audience_id, audience_name, category, reach, engagement_score |
| 4 | 检查 get_raw_table() | 返回 "raw_quorum" |

---

## TC-02: LeadRX Adapter — Mock 数据拉取

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 创建 LeadRXAdapter(credentials={"mock":True}, agency_id) | 实例化成功 |
| 2 | 调用 fetch("2026-03-01", "2026-03-31") | 返回 records 含 conversion_id, touchpoint_channel, attribution_weight |
| 3 | 检查 get_raw_table() | 返回 "raw_leadrx" |

---

## TC-03: LiveRamp Adapter — Mock 数据 + PII 哈希

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 调用 fetch() 获取 mock 数据 | records 含 segment_id, match_type, matched_count |
| 2 | ETLRunner 执行完整流程 | PHI scan 检测到 identity 数据 |
| 3 | 检查写入仓库的数据 | email/device_id 已哈希，segment_name 保留明文 |
| 4 | 检查 get_raw_table() | 返回 "raw_liveramp" |

---

## TC-04: DV360 Adapter — Mock 数据拉取

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 调用 fetch() | 返回 records 含 advertiser_id, campaign_id, campaign_name, impressions, clicks, spend |
| 2 | 检查 get_raw_table() | 返回 "raw_dv360" |

---

## TC-05: StackAdapt Adapter — Mock 数据拉取

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 调用 fetch() | 返回 records 含 campaign_id, creative_id, impressions, clicks, spend |
| 2 | 检查 get_raw_table() | 返回 "raw_stackadapt" |

---

## TC-06: ETLRunner 集成 — 全流程

**每个 adapter 各执行一轮**

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | ETLRunner.run(adapter, start, end, integration_id) | ETLResult.success == True |
| 2 | 检查 records_fetched > 0 | 确认数据拉取成功 |
| 3 | 检查 records_written > 0 | 确认数据写入仓库 |
| 4 | 检查 warehouse.get_sync_state() | 同步状态已更新 |

---

## TC-07: Warehouse 白名单验证

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | warehouse.insert_many("raw_quorum", rows) | 成功 |
| 2 | warehouse.insert_many("raw_leadrx", rows) | 成功 |
| 3 | warehouse.insert_many("raw_liveramp", rows) | 成功 |
| 4 | warehouse.insert_many("raw_dv360", rows) | 成功 |
| 5 | warehouse.insert_many("raw_stackadapt", rows) | 成功 |
| 6 | warehouse.insert_many("raw_unknown", rows) | ValueError |

---

## TC-08: 错误处理

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | adapter.fetch() 抛出网络异常 | ETLResult.errors 非空，sync_state 不更新 |
| 2 | adapter.fetch() 返回格式异常的 record | 该 record 跳过，其余正常写入 |

---

## TC-09: dbt Staging 模型

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 检查 stg_quorum.sql 存在且语法正确 | ✅ |
| 2 | 检查 stg_leadrx.sql 存在且语法正确 | ✅ |
| 3 | 检查 stg_liveramp.sql 存在且语法正确 | ✅ |
| 4 | 检查 stg_dv360.sql 存在且语法正确 | ✅ |
| 5 | 检查 stg_stackadapt.sql 存在且语法正确 | ✅ |
| 6 | 检查 sources.yml 包含所有新 source | ✅ |
