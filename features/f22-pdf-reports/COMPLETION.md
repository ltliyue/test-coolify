# f22-pdf-reports 完成报告

- **完成时间**：2026-04-02
- **功能分支**：feat/f22-pdf-reports
- **测试报告**：[user-test-doc](test/user-test-doc.md)

## 功能摘要

实现 PDF 报告生成引擎，包含 HTML 模板渲染（Jinja2）→ PDF 转换（weasyprint）→ MinIO 上传 → SMTP 邮件发送的完整管道。支持 per-client 调度配置（daily/weekly/monthly）和手动触发。报告内容仅含 Level 0 聚合数据。

## 文件清单

### 新建文件

- `backend/app/models/report.py` — ReportSchedule + ReportHistory ORM
- `backend/app/schemas/report.py` — 7 个 Pydantic schema（含频率/邮箱验证）
- `backend/app/api/v1/reports.py` — 7 个 API 端点（CRUD + generate + history + download）
- `backend/app/services/reports/generator.py` — 数据查询 + HTML 渲染 + PDF 转换 + MinIO 上传
- `backend/app/services/reports/email_sender.py` — SMTP 邮件发送（Mock 模式支持）
- `backend/app/services/reports/templates/report_default.html` — Jinja2 报告模板
- `backend/app/tasks/report_tasks.py` — Celery 异步生成 + 定时调度检查
- `infra/migrations/018_reports.sql` — 2 张 PG 表 + 4 索引
- `backend/tests/test_reports.py` — 11 个测试用例

### 修改文件

- `backend/app/api/v1/router.py` — 注册 reports_router
- `backend/app/core/config.py` — 添加 7 个 SMTP 配置项
- `backend/requirements.txt` — 添加 weasyprint/jinja2/aiosmtplib
- `backend/tests/conftest.py` — 添加 report 表到 TRUNCATE 列表

## 合规修复

- recipients 使用 Fernet 加密存储（`recipients_encrypted` Text 列），API 仅返回 `recipients_count`
- Celery task 查询 schedule 增加 `agency_id` 过滤（租户隔离）
- 定时调度 task 添加系统级审计记录
- error_message 仅保留异常类型名
- SMTP 凭证从环境变量读取，日志不记录密码和收件人
- presigned URL 24 小时过期

## 已知限制 & 后续工作

- [ ] AI 摘要叠加（Phase 2）
- [ ] 自定义 PDF 模板编辑器（Phase 2）
- [ ] MinIO 报告文件自动过期清理 task
- [ ] recipients 纳入 DSAR 数据处理范围
