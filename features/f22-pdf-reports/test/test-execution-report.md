# f22-pdf-reports 测试执行报告

- **测试时间**：2026-04-02
- **测试环境**：pytest + PostgreSQL + weasyprint fallback + SMTP mock
- **测试文件**：`backend/tests/test_reports.py`

## 执行结果

| 测试用例                             | 结果    | 说明                              |
| ------------------------------------ | ------- | --------------------------------- |
| test_render_report_html              | ✅ 通过 | Jinja2 模板渲染含品牌化           |
| test_render_report_empty_campaigns   | ✅ 通过 | 空数据正常渲染                    |
| test_html_to_pdf_fallback            | ✅ 通过 | weasyprint 不可用时 HTML fallback |
| test_schedule_crud                   | ✅ 通过 | 调度完整 CRUD，recipients 加密    |
| test_schedule_invalid_frequency      | ✅ 通过 | frequency 校验                    |
| test_schedule_empty_recipients       | ✅ 通过 | recipients 非空校验               |
| test_generate_report                 | ✅ 通过 | 手动触发生成 pending              |
| test_report_history                  | ✅ 通过 | 历史列表查询                      |
| test_schedule_not_found_other_agency | ✅ 通过 | 404 租户隔离                      |
| test_download_not_found              | ✅ 通过 | 下载不存在的报告                  |
| test_email_sender_mock               | ✅ 通过 | SMTP 未配置时 mock 模式           |

## 测试汇总

- **通过**：11/11
- **失败**：0

## 合规验证

- ✅ recipients 使用 Fernet 加密存储（Text 列），API 仅返回 count
- ✅ 报告内容仅 Level 0 聚合数据（模板页脚明确声明）
- ✅ 7 个 API 端点 + 2 个 Celery task 有审计日志
- ✅ Celery task 查询 schedule 带 agency_id 过滤
- ✅ SMTP 凭证从环境变量读取，日志不记录密码/邮箱
- ✅ presigned URL 24 小时过期
- ✅ error_message 仅异常类型名

## 总结

11 个用例全部通过。PDF 生成 fallback 机制验证通过，weasyprint 未安装时降级为 HTML bytes。SMTP mock 模式验证通过，生产环境需配置 SMTP_HOST 启用真实发送。
