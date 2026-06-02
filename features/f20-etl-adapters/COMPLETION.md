# f20-etl-adapters 完成报告

- **完成时间**：2026-04-02
- **功能分支**：feat/f19-f20-campaigns-etl-adapters
- **测试报告**：[user-test-doc](test/user-test-doc.md)

## 功能摘要

新增 5 个 ETL 数据适配器（Quorum / LeadRX / LiveRamp / DV360 / StackAdapt），补齐 MVP P1 和 P2 优先级的外部平台数据拉取能力。所有 adapter 继承 BaseAdapter 模式，含 mock 数据开发模式、PII 哈希处理、DuckDB schema 和 dbt staging 模型。

## 文件清单

### 新建文件

- `backend/app/services/etl/adapters/quorum.py` — Quorum 受众行为数据（Daily，API Key）
- `backend/app/services/etl/adapters/leadrx.py` — LeadRX 归因数据（1h，分页，conversion_id 哈希）
- `backend/app/services/etl/adapters/liveramp.py` — LiveRamp 身份解析（Daily，segment_id 哈希）
- `backend/app/services/etl/adapters/dv360.py` — DV360 programmatic campaign（1h，advertiser_id 验证）
- `backend/app/services/etl/adapters/stackadapt.py` — StackAdapt native ad（1h，分页）
- `dbt/models/staging/stg_quorum.sql` — Quorum staging 模型
- `dbt/models/staging/stg_leadrx.sql` — LeadRX staging 模型
- `dbt/models/staging/stg_liveramp.sql` — LiveRamp staging 模型
- `dbt/models/staging/stg_dv360.sql` — DV360 staging 模型
- `dbt/models/staging/stg_stackadapt.sql` — StackAdapt staging 模型
- `backend/tests/test_etl_new_adapters.py` — 18 个测试用例
- `features/f20-etl-adapters/requirement/requirement-doc.md` — 需求文档
- `features/f20-etl-adapters/design/dev-design-doc.md` — 设计文档
- `features/f20-etl-adapters/test/user-test-doc.md` — 测试文档

### 修改文件

- `backend/app/core/warehouse_client.py` — +5 张 raw 表到 `_ALLOWED_TABLES` + DuckDB schema（无 raw_json）
- `backend/app/services/etl/runner.py` — 匿名化改为无条件执行（C-2 合规修复）
- `dbt/models/staging/sources.yml` — +5 个 source 定义

## 合规修复（安全审查后）

- 所有 5 个 adapter 移除 `raw_json` 字段（C-1：防止 PII 绕过检测层泄漏到仓库）
- ETL Runner 无条件执行 `anonymize_record_for_warehouse()`（C-2：不再依赖 PHI 检测触发）
- LiveRamp adapter 覆写 `transform()`：`segment_id` 经 `hash_identifier()` 哈希（C-3）
- LeadRX adapter 覆写 `transform()`：`conversion_id` 经 `hash_identifier()` 哈希（C-4）
- DV360 adapter 增加 `advertiser_id` 正则验证（H-4：SSRF 防护）

## 已知限制 & 后续工作

- [ ] LiveRamp 合同状态待确认（Dev Brief 标注 confirm contract）
- [ ] 真实 API 集成测试（当前仅 mock 模式验证）
- [ ] Shopify adapter 未实现（MVP P2 优先级，需求未明确）
- [ ] TikTok Ads adapter 未实现（已在 platform_registry 注册，ETL adapter 待开发）
