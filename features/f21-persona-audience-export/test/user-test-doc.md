# f21-persona-audience-export 用户测试文档

> 版本：v1.0 | 日期：2026-04-02

## TC-01: 导出预览

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | GET `/personas/{id}/export-audience/preview?platform=meta_ads` | 200, 返回 targeting_spec + warnings |
| 2 | 确认 targeting_spec 不含 email/phone/name 等 PII | ✅ 仅含聚合属性 |
| 3 | persona 无 psychographics 时预览 | 200, warnings 非空 |

## TC-02: Meta Ads 导出

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | POST `/personas/{id}/export-audience` body: `{platform: "meta_ads"}` | 201, status=pending |
| 2 | Celery task 执行（mock 模式） | export 更新为 success + external_audience_id |
| 3 | GET `/personas/{id}/export-audience` | 200, 含导出记录 |

## TC-03: DV360 导出

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | POST `/personas/{id}/export-audience` body: `{platform: "dv360"}` | 201, status=pending |
| 2 | mock 执行后检查 | success + external_audience_id |

## TC-04: 无效参数

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | POST 不存在的 persona_id | 404 |
| 2 | POST platform="invalid" | 400 |
| 3 | 未认证请求 | 401 |

## TC-05: 租户隔离

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | agency_A 用户导出 agency_B 的 persona | 404 |
| 2 | agency_A 列出 exports | 仅看到自己的记录 |

## TC-06: 审计日志

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 执行导出后检查 audit_logs | 含 persona_export action |

## TC-07: PII 过滤验证

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | persona psychographics 含 email 字段 | targeting_spec 中不含该字段 |
