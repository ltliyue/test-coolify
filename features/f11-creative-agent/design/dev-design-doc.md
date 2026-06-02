# f11-creative-agent 设计文档

## 架构概览

```
POST /creatives/generate {persona_id, platforms, brand_config_id}
  ↓
build_shared_context + 注入 persona 数据
  ↓
creative_agent.run()
  ↓
Core AI Brain → Claude Sonnet (CREATIVE_MODEL)
  ↓
per-platform 循环：生成 headline / body / cta / image_prompt
  ↓
Generation (主记录) + N GenerationResult (每平台一个)
```

## 核心文件

| 文件                                      | 职责                                                |
| ----------------------------------------- | --------------------------------------------------- |
| `models/creative.py`                      | Generation + GenerationResult（1:N）                |
| `schemas/creative.py`                     | GenerationCreate + GenerationResponse + 嵌套 Result |
| `api/v1/creatives.py`                     | 3 端点                                              |
| `services/ai/agents/creative.py`          | Creative Agent（167 行，四平台 prompt）             |
| `infra/migrations/010_creative_agent.sql` | generations + generation_results 表                 |

## 数据模型

```
Generation (主):
  id UUID PK
  agency_id UUID NOT NULL
  persona_id UUID FK
  agent_type VARCHAR = 'creative'
  input_metadata JSONB

GenerationResult (子, N per Generation):
  id UUID PK
  generation_id FK
  platform VARCHAR  — meta_ads / dv360 / tiktok_ads / google_ads
  headline / body / cta
  image_prompt TEXT
```

## 关键决策

- **1:N 关系**：一次请求生成多平台变体，统一 Generation 记录便于对比
- **平台格式约束**：每平台有字符数限制（Meta headline 40 / TikTok description 100 等）
- **Persona 上下文注入**：Creative agent 读取 persona.psychographics + recommended_tone
- **品牌合规**：规则式 filter（禁用词、颜色）在 prompt 中约束，Phase 2 加 AI 评分
