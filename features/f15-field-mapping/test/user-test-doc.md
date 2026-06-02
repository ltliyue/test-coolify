# f15-field-mapping 用户测试文档

测试文件：`backend/tests/test_field_mappings.py`（14 用例）

## TC-01: CRUD

| 步骤      | 预期                 |
| --------- | -------------------- |
| POST      | 201, version=1       |
| GET /{id} | 200                  |
| PUT       | 200, version=2       |
| DELETE    | 204, is_active=false |

## TC-02: 版本管理

| 步骤                      | 预期                           |
| ------------------------- | ------------------------------ |
| GET /{id}/versions        | 200, 所有历史                  |
| POST /{id}/rollback/{v=1} | 200, 创建 version=3（复制 v1） |

## TC-03: 平台过滤

| 步骤              | 预期        |
| ----------------- | ----------- |
| GET ?platform=ga4 | 仅 GA4 映射 |

## TC-04: Canonical Schema

| 步骤                                 | 预期              |
| ------------------------------------ | ----------------- |
| GET /field-mappings/canonical-schema | 200, 24 字段      |
| GET ?platform=meta_ads               | Meta raw 字段列表 |

## TC-05: 模板

| 步骤                              | 预期          |
| --------------------------------- | ------------- |
| GET /templates/{platform}/default | 200, 默认映射 |
| GET /templates/invalid/default    | 404           |

## TC-06: Transform 预览

| 步骤                                | 预期                |
| ----------------------------------- | ------------------- |
| POST /preview {config, sample_data} | 200, 返回变换后记录 |

## TC-07: 空 list

| 步骤                             | 预期    |
| -------------------------------- | ------- |
| GET /field-mappings（新 agency） | 200, [] |

## TC-08: 认证

| 步骤     | 预期 |
| -------- | ---- |
| 无 token | 401  |
