# P1 核心模块测试执行报告（F-06 / F-07 / F-08 / F-09）

- **测试时间**：2026-03-31
- **测试环境**：macOS，Python 3.9.6，PostgreSQL（receptiviq@localhost:5432/receptiviq），DuckDB 内存模式
- **测试命令**：`PYTHONPATH=. DATABASE_URL=postgresql+asyncpg://receptiviq:receptiviq@localhost:5432/receptiviq python3 -m pytest tests/ -v`
- **测试结果**：✅ 52/52 通过（含 P0 回归），0 失败，0 跳过

---

## 测试用例执行明细

### F-08：WarehouseClient DuckDB 模式（test_warehouse.py）

| #   | 测试用例                             | 结果      | 说明                                              |
| --- | ------------------------------------ | --------- | ------------------------------------------------- |
| 1   | `test_duckdb_schema_initialized`     | ✅ PASSED | 连接后 4 张 raw 表自动创建                        |
| 2   | `test_insert_many_ga4`               | ✅ PASSED | 向 raw_ga4_events 插入 1 条，agency_id 注入正确   |
| 3   | `test_insert_many_meta_ads`          | ✅ PASSED | 向 raw_meta_ads 批量插入 2 条                     |
| 4   | `test_insert_many_empty`             | ✅ PASSED | 空列表不写入，返回 0                              |
| 5   | `test_query_returns_dict_list`       | ✅ PASSED | query() 返回 dict 列表，参数化查询正确            |
| 6   | `test_sync_state_create_and_update`  | ✅ PASSED | 首次创建 → 再次更新 sync_state，cursor/count 正确 |
| 7   | `test_sync_state_different_agencies` | ✅ PASSED | 不同 agency 的 sync_state 互不干扰                |

### F-06：ETL 管道框架（test_etl.py）

| #   | 测试用例                                        | 结果      | 说明                                               |
| --- | ----------------------------------------------- | --------- | -------------------------------------------------- |
| 8   | `test_ga4_adapter_mock_returns_data`            | ✅ PASSED | GA4 mock 返回 1 条 synthetic 记录                  |
| 9   | `test_ga4_adapter_get_raw_table`                | ✅ PASSED | 目标表为 raw_ga4_events                            |
| 10  | `test_meta_ads_adapter_mock_returns_data`       | ✅ PASSED | Meta Ads mock 返回 1 条 synthetic 记录             |
| 11  | `test_meta_ads_adapter_get_raw_table`           | ✅ PASSED | 目标表为 raw_meta_ads                              |
| 12  | `test_hubspot_adapter_mock_returns_data`        | ✅ PASSED | HubSpot mock 返回 2 条 synthetic 联系人记录        |
| 13  | `test_hubspot_adapter_get_raw_table`            | ✅ PASSED | 目标表为 raw_hubspot_contacts                      |
| 14  | `test_etl_runner_ga4_end_to_end`                | ✅ PASSED | 端到端：fetch→PHI→transform→load→sync_state 全流程 |
| 15  | `test_etl_runner_meta_ads_end_to_end`           | ✅ PASSED | Meta Ads 端到端，agency_id 正确注入                |
| 16  | `test_etl_runner_hubspot_end_to_end`            | ✅ PASSED | HubSpot 端到端，2 条联系人写入                     |
| 17  | `test_etl_runner_clean_record_passes_phi_check` | ✅ PASSED | 无 PHI 字段的 mock 记录直接通过，skipped=0         |
| 18  | `test_etl_runner_multiple_platforms_isolated`   | ✅ PASSED | GA4/Meta Ads 各写各自表，互不干扰                  |

### F-09：AI Brain API（test_ai.py）

| #   | 测试用例                                       | 结果      | 说明                                                      |
| --- | ---------------------------------------------- | --------- | --------------------------------------------------------- |
| 19  | `test_ai_chat_requires_auth`                   | ✅ PASSED | 无 token 访问 /ai/chat 返回 401/403                       |
| 20  | `test_ai_usage_requires_auth`                  | ✅ PASSED | 无 token 访问 /ai/usage/monthly 返回 401/403              |
| 21  | `test_ai_chat_success`                         | ✅ PASSED | 有 token 时 200，响应含 agent_type/result/model/budget    |
| 22  | `test_ai_chat_budget_remaining_reflects_usage` | ✅ PASSED | 无真实 LLM 调用时 budget_remaining = monthly_token_budget |
| 23  | `test_ai_chat_budget_exceeded`                 | ✅ PASSED | 用量超出预算时返回 429，detail.code=BUDGET_EXCEEDED       |
| 24  | `test_ai_usage_monthly_structure`              | ✅ PASSED | 月度摘要结构完整，空用量 total_tokens=0                   |
| 25  | `test_ai_usage_monthly_with_records`           | ✅ PASSED | 2 条 usage 记录后，聚合 by_model/by_agent 准确            |

### P0 回归（test_auth.py / test_compliance.py / test_integrations.py / test_tenants.py）

| 范围        | 通过数 | 说明                |
| ----------- | ------ | ------------------- |
| F-02 认证   | 6/6    | 无回归，P0 全部正常 |
| F-00 合规   | 10/10  | 无回归，P0 全部正常 |
| F-05 集成   | 6/6    | 无回归，P0 全部正常 |
| F-01 多租户 | 5/5    | 无回归，P0 全部正常 |

---

## 总结

所有 P1 优先级模块（F-06 / F-08 / F-09）的测试均已通过，dbt 转换层（F-07）为纯 SQL 文件，不进行 pytest 测试：

- **F-08 WarehouseClient**：DuckDB 内存模式完整验证，4 表 schema 自动初始化，insert_many/query/sync_state 全部正常
- **F-06 ETL 管道**：GA4 / Meta Ads / HubSpot 三个 mock 适配器端到端测试全通过，PHI 检测集成验证
- **F-09 AI Brain API**：POST /ai/chat 基本流程 + 预算超限 429 + 月度用量聚合全部验证
- **F-07 dbt 转换层**：staging（stg_ga4 / stg_meta_ads / stg_hubspot）+ canonical + mart 模型文件已创建，待 Snowflake/DuckDB dbt 执行验证
- **P0 全部 27 个测试无回归**

**全量：52/52 通过（25 新增 + 27 P0 回归）**
