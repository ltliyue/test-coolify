# f20-etl-adapters 测试执行报告

- **测试时间**：2026-04-02
- **测试环境**：pytest + DuckDB（内存）+ mock 凭证
- **测试文件**：`backend/tests/test_etl_new_adapters.py`

## 执行结果

| 测试用例                                    | 结果    | 说明                   |
| ------------------------------------------- | ------- | ---------------------- |
| test_quorum_adapter_mock                    | ✅ 通过 | Quorum mock 数据拉取   |
| test_quorum_adapter_raw_table               | ✅ 通过 | raw_quorum 表名正确    |
| test_quorum_etl_end_to_end                  | ✅ 通过 | ETL 完整流程 + 入仓    |
| test_leadrx_adapter_mock                    | ✅ 通过 | LeadRX mock 数据       |
| test_leadrx_adapter_raw_table               | ✅ 通过 | raw_leadrx 表名        |
| test_leadrx_etl_end_to_end                  | ✅ 通过 | conversion_id 哈希验证 |
| test_liveramp_adapter_mock                  | ✅ 通过 | LiveRamp mock 数据     |
| test_liveramp_adapter_raw_table             | ✅ 通过 | raw_liveramp 表名      |
| test_liveramp_etl_end_to_end                | ✅ 通过 | segment_id 哈希验证    |
| test_dv360_adapter_mock                     | ✅ 通过 | DV360 mock 数据        |
| test_dv360_adapter_raw_table                | ✅ 通过 | raw_dv360 表名         |
| test_dv360_etl_end_to_end                   | ✅ 通过 | programmatic 数据入仓  |
| test_stackadapt_adapter_mock                | ✅ 通过 | StackAdapt mock 数据   |
| test_stackadapt_adapter_raw_table           | ✅ 通过 | raw_stackadapt 表名    |
| test_stackadapt_etl_end_to_end              | ✅ 通过 | native ad 数据入仓     |
| test_warehouse_whitelist_accepts_new_tables | ✅ 通过 | 5 张新表加入白名单     |
| test_warehouse_whitelist_rejects_unknown    | ✅ 通过 | 未知表名被拒绝         |
| test_all_new_adapters_isolated              | ✅ 通过 | 5 个 adapter 互不干扰  |

## 测试汇总

- **通过**：18/18
- **失败**：0

## 合规验证

- ✅ 所有 adapter 无 `raw_json` 字段（PII 泄漏风险已清除）
- ✅ ETL Runner 无条件匿名化（规则 2）
- ✅ LiveRamp segment_id、LeadRX conversion_id 经 `hash_identifier()` 哈希
- ✅ DV360 advertiser_id 正则验证（SSRF 防护）
- ✅ 新增 5 张 raw 表加入 `_ALLOWED_TABLES` 白名单

## 总结

5 个 ETL adapter 全部通过 mock 模式测试。真实 API 集成测试需要有效凭证，留待 Phase 2 端到端验证。
