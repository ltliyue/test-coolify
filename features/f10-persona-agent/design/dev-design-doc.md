# f10-persona-agent 设计文档

## 架构概览

```
POST /personas/generate
  ↓
build_shared_context(agency_id) — 组装品牌配置 + token 预算 + 历史摘要
  ↓
persona_agent.run(request, context)
  ↓
Core AI Brain → OpenRouter → Claude Opus (PERSONA_MODEL)
  ↓
解析 JSON → 批量创建 Persona ORM → 返回 PersonaResponse[]
```

## 核心文件

| 文件                                     | 职责                                            |
| ---------------------------------------- | ----------------------------------------------- |
| `models/persona.py`                      | Persona ORM（agency_id NOT NULL, L-01）         |
| `schemas/persona.py`                     | Create/Update/Response + PersonaGenerateRequest |
| `api/v1/personas.py`                     | 6 端点 + audit 全覆盖                           |
| `services/ai/agents/persona.py`          | Persona Agent（148 行）                         |
| `infra/migrations/009_persona_agent.sql` | agency_id / source / model_used / is_active     |

## 数据模型

```
Persona:
  id UUID PK
  agency_id UUID FK NOT NULL (L-01 强制隔离)
  client_account_id UUID nullable (legacy)
  name, description, recommended_tone
  psychographics JSON  — 心理/行为特征
  channel_preferences JSON — 渠道偏好
  source VARCHAR  — 'manual' | 'ai'
  model_used VARCHAR nullable
  is_active BOOL (软删除)
```

## 关键决策

- **结构化输出**：AI 返回 JSON schema，而非自由文本
- **软删除**：is_active=false 而非 DELETE（保留审计）
- **Token 预算前置检查**：budget_remaining<=0 即 429，不调用 LLM
- **Mock 模式**：OPENROUTER_API_KEY 空时返回固定 mock persona

## AI Prompt 模板

位于 `services/ai/agents/persona.py` system prompt：

- 输入：品牌配置 + 用户 prompt
- 要求输出 3-7 个命名画像
- JSON 格式强约束（便于解析）
