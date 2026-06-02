# f15-field-mapping 设计文档

## 架构概览

```
POST /field-mappings     — 创建 + 产生 version 1
PUT /field-mappings/{id} — 更新 + version+=1 + 旧版本归档
POST rollback/{version}  — 恢复历史版本

TransformEngine:
  raw record → apply(mapping_config) → canonical record
    支持 4 种变换：
    - direct:           source_field → target_field
    - value_mapping:    {"lead":"new_lead", ...}
    - unit_conversion:  cents → dollars
    - formula:          source_a + source_b → target
```

## 核心文件

| 文件                                         | 职责                                        |
| -------------------------------------------- | ------------------------------------------- |
| `models/field_mapping.py`                    | FieldMapping + FieldMappingVersion（1:N）   |
| `schemas/field_mapping.py`                   | 含大小限制（L-02：4KB config, 200 条/次）   |
| `api/v1/field_mappings.py`                   | 10 端点（CRUD + 版本 + 回滚 + 预览 + 模板） |
| `services/field_mapping/canonical_schema.py` | 24 字段定义（6 类别）                       |
| `services/field_mapping/transform.py`        | TransformEngine                             |
| `services/field_mapping/template_loader.py`  | JSON 模板加载                               |
| `services/field_mapping/templates/*.json`    | 6 平台模板                                  |

## Canonical Schema 6 类别

| 类别        | 字段示例                            |
| ----------- | ----------------------------------- |
| time        | date, timestamp, period             |
| identity    | user_id_hash, session_id            |
| performance | impressions, clicks, spend          |
| engagement  | sessions, page_views, bounce_rate   |
| revenue     | conversions, conversion_value, roas |
| custom      | tags, dimensions                    |

## 关键决策

- **版本即快照**：每次 PUT 产生 FieldMappingVersion，config 完整保存
- **回滚策略**：POST rollback 创建新 version（内容复制自指定历史版本）
- **预览不保存**：preview 端点接受临时 config + 示例数据，返回变换结果
- **声明式规则**：transform config 是 JSON，无可执行代码（合规）
