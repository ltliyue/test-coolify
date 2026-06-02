# f10-persona-agent 用户测试文档

测试文件：`backend/tests/test_personas.py`（9 用例）

## TC-01: 空列表

| 步骤                       | 预期    |
| -------------------------- | ------- |
| GET /personas（新 agency） | 200, [] |

## TC-02: 手动创建

| 步骤                                 | 预期               |
| ------------------------------------ | ------------------ |
| POST /personas name + psychographics | 201, source=manual |

## TC-03: AI 生成（Mock 模式）

| 步骤                            | 预期                   |
| ------------------------------- | ---------------------- |
| POST /personas/generate count=3 | 200, 返回 3 个 persona |
| source=ai, model_used 非空      | ✅                     |

## TC-04: CRUD

| 步骤               | 预期                 |
| ------------------ | -------------------- |
| GET /personas/{id} | 200                  |
| GET 不存在 id      | 404                  |
| PUT 更新字段       | 200                  |
| DELETE             | 204, is_active=false |

## TC-05: 过滤

| 步骤                        | 预期       |
| --------------------------- | ---------- |
| GET /personas?source=ai     | 仅 AI 生成 |
| GET /personas?source=manual | 仅手动     |

## TC-06: 认证

| 步骤          | 预期 |
| ------------- | ---- |
| 无 token 访问 | 401  |
