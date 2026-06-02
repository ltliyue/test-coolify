# f19-campaigns 用户测试文档

> 版本：v1.0 | 日期：2026-04-02

## 测试环境

- Backend: FastAPI + pytest-asyncio
- Database: PostgreSQL (test) + DuckDB (warehouse mock)
- 前置数据: agency + user + integration 已创建

---

## TC-01: 获取跨平台 Campaign 列表

**前置条件**：仓库中已有 meta_ads 和 dv360 的 campaign 数据

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | GET `/api/v1/campaigns` | 200, 返回含 meta_ads 和 dv360 的 campaign 列表 |
| 2 | GET `/api/v1/campaigns?platform=meta_ads` | 200, 仅返回 meta_ads 的 campaign |
| 3 | GET `/api/v1/campaigns?date_from=2026-03-01&date_to=2026-03-31` | 200, 仅返回指定日期范围内的数据 |
| 4 | GET `/api/v1/campaigns?limit=2&offset=0` | 200, 返回最多 2 条 |

**验收标准**：FR-1 统一 Campaign 视图

---

## TC-02: 获取聚合摘要

**前置条件**：仓库中已有多平台 campaign 数据

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | GET `/api/v1/campaigns/summary` | 200, 含 total_spend, total_conversions, platform_breakdown |
| 2 | GET `/api/v1/campaigns/summary?view=client` | 200, 字段名简化（面向客户展示） |
| 3 | GET `/api/v1/campaigns/summary?client_id={id}` | 200, 仅返回该客户的数据 |

**验收标准**：FR-3 跨平台聚合摘要

---

## TC-03: 单 Campaign 时序指标

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | GET `/api/v1/campaigns/meta_ads/{ext_id}/metrics` | 200, 返回按日时序数据 |
| 2 | GET `/api/v1/campaigns/invalid_platform/{ext_id}/metrics` | 400, 无效平台 |
| 3 | GET `/api/v1/campaigns/meta_ads/nonexistent/metrics` | 200, 返回空列表 |

---

## TC-04: Budget Config CRUD

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | POST `/api/v1/campaigns/budget-configs` body: `{platform, external_campaign_id, daily_budget: 100}` | 201, 返回创建的配置 |
| 2 | GET `/api/v1/campaigns/budget-configs` | 200, 含刚创建的配置 |
| 3 | PUT `/api/v1/campaigns/budget-configs/{id}` body: `{daily_budget: 200}` | 200, budget 更新为 200 |
| 4 | DELETE `/api/v1/campaigns/budget-configs/{id}` | 204 |
| 5 | POST 重复的 `(platform, external_campaign_id)` | 409, 唯一约束冲突 |

**验收标准**：FR-2 Budget Pacing Alerts（配置部分）

---

## TC-05: Budget Pacing 告警触发

**前置条件**：已创建 budget config (daily_budget=100, threshold=0.15)，仓库中该 campaign 当日 spend=130

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 手动触发 `check_budget_pacing` task | 检测到超支 30%（>15% 阈值） |
| 2 | GET `/api/v1/campaigns/budget-alerts` | 200, 含一条超支告警 |
| 3 | 修改 config `alert_enabled=false`，再次触发 task | 不产生新告警 |

---

## TC-06: 租户隔离

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 用 agency_A 的 token 访问 campaigns | 仅看到 agency_A 的数据 |
| 2 | 用 agency_A 的 token 操作 agency_B 的 budget config | 404 |

---

## TC-07: 仓库不可用降级

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 仓库连接断开时 GET `/api/v1/campaigns` | 503, 友好错误消息 |
| 2 | Budget config CRUD（PG）不受影响 | 正常 200/201 |
