# f22-pdf-reports 用户测试文档

## TC-01: 报告调度 CRUD

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | POST `/reports/schedules` | 201, 创建调度 |
| 2 | GET `/reports/schedules` | 200, 含创建的调度 |
| 3 | PUT `/reports/schedules/{id}` | 200, 更新成功 |
| 4 | DELETE `/reports/schedules/{id}` | 204 |

## TC-02: 手动触发报告生成

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | POST `/reports/generate` | 201, status=pending |
| 2 | 检查 report_history | 含生成记录 |
| 3 | 报告内容仅含 Level 0 数据 | 无 PII/PHI |

## TC-03: 报告历史 + 下载

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | GET `/reports/history` | 200, 含历史记录 |
| 2 | GET `/reports/history/{id}/download` | 200, 含 presigned URL |

## TC-04: 租户隔离

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | agency_A 访问 agency_B 的调度 | 404 |
| 2 | agency_A 下载 agency_B 的报告 | 404 |

## TC-05: 审计日志

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 所有端点操作后检查 audit_logs | 含 report.* action |

## TC-06: 无效参数

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | frequency="invalid" | 400 |
| 2 | recipients=[] | 400 |
| 3 | 未认证 | 401 |
