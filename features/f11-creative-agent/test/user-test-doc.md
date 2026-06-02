# f11-creative-agent 用户测试文档

测试文件：`backend/tests/test_creatives.py`（8 用例）

## TC-01: 生成四平台创意

| 步骤                                                                      | 预期 |
| ------------------------------------------------------------------------- | ---- |
| POST /creatives/generate platforms=[meta_ads,dv360,tiktok_ads,google_ads] | 201  |
| 返回 Generation 含 4 个 GenerationResult                                  | ✅   |

## TC-02: 创意内容检查

| 字段         | 预期       |
| ------------ | ---------- |
| headline     | 非空字符串 |
| body         | 非空       |
| cta          | 非空       |
| image_prompt | 非空       |

## TC-03: 指定平台子集

| 步骤                      | 预期                |
| ------------------------- | ------------------- |
| POST platforms=[meta_ads] | 201, 仅 1 个 result |

## TC-04: 列表 + 详情

| 步骤                | 预期             |
| ------------------- | ---------------- |
| GET /creatives      | 200              |
| GET /creatives/{id} | 200 含 results[] |
| GET 不存在          | 404              |

## TC-05: 租户隔离

| 测试                         | 预期 |
| ---------------------------- | ---- |
| 另一 agency 的 generation_id | 404  |

## TC-06: 认证

| 步骤     | 预期 |
| -------- | ---- |
| 无 token | 401  |
