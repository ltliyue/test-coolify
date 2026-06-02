# p1-etl-warehouse-ai 用户测试文档

聚合测试：`test_etl.py`（11）+ `test_warehouse.py`（7）+ `test_ai.py`（7）+ `test_field_mappings.py`（14） = 39 用例（新增 etl_new_adapters 18 已独立）

## TC-01: ETL Runner 端到端

| 平台         | 预期                             |
| ------------ | -------------------------------- |
| GA4 mock     | records_written=1                |
| Meta mock    | records_written=1                |
| HubSpot mock | records_written=2（含 2 联系人） |

## TC-02: 仓库白名单防注入

| 测试               | 预期                     |
| ------------------ | ------------------------ |
| insert_many 已知表 | 成功                     |
| insert_many 未知表 | ValueError               |
| DROP TABLE 语句    | ValueError（白名单拒绝） |

## TC-03: Sync State 追踪

| 步骤                   | 预期                               |
| ---------------------- | ---------------------------------- |
| 首次 update_sync_state | 创建记录                           |
| 二次 update            | 覆盖 last_cursor + records_written |
| 多 agency 数据         | 互相隔离                           |

## TC-04: AI Chat

| 步骤                      | 预期                      |
| ------------------------- | ------------------------- |
| POST /ai/chat             | 200, 含 response + tokens |
| 超出 monthly_token_budget | 429                       |
| 未认证                    | 401                       |

## TC-05: Token 用量统计

| 步骤                      | 预期                             |
| ------------------------- | -------------------------------- |
| GET /ai/usage/monthly     | 200, 含 by_model / by_agent 聚合 |
| budget_remaining 正确扣减 | ✅                               |

## TC-06: 字段映射 CRUD

| 步骤                   | 预期           |
| ---------------------- | -------------- |
| POST /field-mappings   | 201            |
| PUT 产生新 version     | version+=1     |
| POST rollback/{v}      | 恢复历史       |
| GET canonical schema   | 24 字段        |
| POST preview transform | 返回变换后数据 |
