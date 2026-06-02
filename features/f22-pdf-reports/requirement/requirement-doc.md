# f22-pdf-reports 需求文档

> 来源：Dev Brief v2 §Pillar 3 (Automated Report Delivery) + §Client Portal
> 状态：MVP — 模板化 PDF + 定时调度 + 邮件发送

## 功能概述

自动生成 campaign 绩效 PDF 报告并按配置频率发送给客户。Rose 原话："auto-sent from this tool to them and that's all they care about"。MVP 使用模板渲染，Phase 2 增加 AI 摘要叠加。

## MVP 功能需求

### FR-1: PDF 报告生成

- 使用 HTML 模板渲染 campaign 绩效数据为 PDF
- 数据来源：mart_campaign_unified（仓库）+ attribution 报告
- 支持客户品牌配置（logo/colors 注入模板）
- 生成的 PDF 上传到 MinIO，返回 presigned download URL

### FR-2: 报告调度配置

- per-client 配置报告频率（daily/weekly/monthly）
- 配置接收邮箱列表（多个邮箱）
- 配置包含的 metric 范围
- 可手动触发一次性报告生成

### FR-3: 邮件发送

- Celery 定时任务按调度频率触发
- 生成 PDF → 上传 MinIO → 发送邮件（附 download link）
- 邮件发送使用 SMTP（可配置）
- 发送失败自动重试 2 次

### FR-4: 报告历史记录

- 跟踪每次报告生成的状态、接收人、下载链接
- 支持查看历史报告列表

## 合规要求

- 报告内容仅含 Level 0 聚合数据（无 PII/PHI）
- 报告文件有过期时间（presigned URL 24小时有效）
- 邮件发送记录审计日志（含 agency_id、recipient_count、report_type）
- SMTP 凭证从环境变量读取，不硬编码
- 邮件 recipient 列表不含 Level 2+ PII（仅配置的业务邮箱）

## Out of MVP Scope

- AI 摘要叠加（Phase 2）
- 自定义 PDF 模板编辑器（Phase 2）
- 报告内嵌交互图表（Phase 2）
