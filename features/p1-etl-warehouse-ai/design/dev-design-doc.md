# p1-etl-warehouse-ai 设计文档

## 架构概览

```
Platform API → Adapter.fetch()
  ↓
ETLRunner: PHI scan → anonymize (无条件) → transform → warehouse.insert_many()
  ↓
DuckDB/Snowflake raw_* 表
  ↓ dbt: staging → canonical → marts
  ↓
CampaignQueryService / AttributionAgent / PersonaAgent

并行: AI 请求 → brain.py → OpenRouter → token_usage 追踪 → Response
```

## 核心文件

| 文件                                                   | 职责                                |
| ------------------------------------------------------ | ----------------------------------- |
| `services/etl/base.py`                                 | BaseAdapter ABC + ETLResult         |
| `services/etl/runner.py`                               | ETLRunner（PHI + anonymize + 仓库） |
| `services/etl/adapters/*.py`                           | GA4/Meta/HubSpot（3 个初始）        |
| `core/warehouse_client.py`                             | 双后端 + SQL 白名单（H-02/H-03）    |
| `services/ai/brain.py`                                 | LLM 路由 + token_usage + 预算       |
| `services/ai/context.py`                               | SharedContext 组装                  |
| `services/ai/agents/{persona,creative,attribution}.py` | 三 agent                            |
| `services/field_mapping/*.py`                          | TransformEngine + 24 字段 + 6 模板  |

## 关键决策

- **仓库双后端**：`WAREHOUSE_BACKEND` 环境变量切换，SQL 语法兼容
- **SQL 注入防护**：`_ALLOWED_SQL_PREFIXES` 白名单 + `_ALLOWED_TABLES` + 正则列名
- **ETL 合规**：每条记录经 scan_record + **无条件** anonymize_record_for_warehouse（C-2）
- **LLM 路由**：per-agent 模型配置（PERSONA_MODEL=Opus，其余 Sonnet）
- **Mock fallback**：OPENROUTER_API_KEY 为空时返回 mock 数据
- **Token 预算**：Agency.monthly_token_budget 耗尽返回 429

## dbt 模型层级

```
staging/stg_{ga4,meta_ads,hubspot,quorum,leadrx,liveramp,dv360,stackadapt}
canonical/canonical_events
marts/mart_{campaign_performance,campaign_unified,persona_signals,attribution}
```
