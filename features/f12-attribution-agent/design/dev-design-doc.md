# f12-attribution-agent 设计文档

## 架构概览

```
POST /attribution/generate {date_from, date_to, client_id?}
  ↓
查询仓库：canonical_events + mart_attribution
  ↓
attribution_agent.run(context + 聚合数据)
  ↓
Core AI Brain → Claude Sonnet (ATTRIBUTION_MODEL)
  ↓
返回 channels[] + results[] + insights 文本
  ↓
AttributionReport ORM 持久化
```

## 核心文件

| 文件                                         | 职责                                            |
| -------------------------------------------- | ----------------------------------------------- |
| `models/attribution.py`                      | AttributionReport ORM（channels/results JSONB） |
| `schemas/attribution.py`                     | ReportCreate / Response                         |
| `api/v1/attribution.py`                      | 3 端点                                          |
| `services/ai/agents/attribution.py`          | Attribution Agent（220 行）                     |
| `infra/migrations/012_attribution_agent.sql` | attribution_reports 表                          |
| `dbt/models/marts/mart_attribution.sql`      | 渠道贡献度聚合                                  |

## 数据模型

```
AttributionReport:
  id UUID PK
  agency_id UUID NOT NULL
  client_id UUID nullable
  date_from / date_to DATE
  channels JSONB    — [{channel, contribution_pct, cost_per_outcome}]
  results JSONB     — 明细 touchpoint 数据
  insights TEXT     — AI 生成的 plain English 摘要
  created_at
```

## 关键决策

- **JSONB 存储聚合结果**：channels/results 结构随归因模型变化，JSONB 灵活
- **AI 洞察摘要**：insights 字段独立存储，Client View 使用
- **多触点模型**：Last-touch / First-touch / Linear / Time-decay
- **仓库只读**：所有数据从 mart_attribution 查询，不修改仓库
