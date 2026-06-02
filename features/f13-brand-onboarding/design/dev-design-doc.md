# f13-brand-onboarding 设计文档

## 架构概览

```
GET /brands    → 返回当前 agency/client 的 brand_config
PUT /brands    → PATCH 语义（深度合并）
DELETE /brands → 重置为空
  ↓
agencies.brand_config JSONB  (default: empty dict)
clients.brand_config JSONB  (nullable, 覆盖 agency)
  ↓
消费方：Creative Agent / Report Engine / Client Portal
```

## 核心文件

| 文件                                    | 职责                                        |
| --------------------------------------- | ------------------------------------------- |
| `api/v1/brands.py`                      | 3 端点（GET/PUT/DELETE）                    |
| `schemas/brand.py`                      | BrandConfigUpdate / BrandConfigResponse     |
| `infra/migrations/007_brand_config.sql` | brand_config JSONB 列（agencies + clients） |

## 数据结构

```json
{
  "colors": { "primary": "#2E75B6", "secondary": "#FF5733" },
  "fonts": { "primary": "Arial", "heading": "Georgia" },
  "tone": "professional, friendly",
  "logo_url": "https://...",
  "voice": ["confident", "approachable"],
  "prohibited_terms": ["competitor", "cheap"],
  "regulatory_flags": { "hipaa": true, "coppa": false }
}
```

## 关键决策

- **JSONB 存储**：Schema 灵活演进，客户配置差异大
- **PATCH 语义**：深度合并而非全量替换（单字段更新不影响其他）
- **Client 覆盖 Agency**：Client 有配置时优先，否则回退 Agency
- **大小限制 4KB**（L-02 合规）：防止滥用存储
- **无文件上传**：MVP 仅 JSON PUT，Phase 2 加 PDF/图片解析

## Phase 2 扩展

- PDF/图片品牌手册上传（MinIO）
- AI 自动提取色彩/字体/语调
- 客户自服务入驻 UI
