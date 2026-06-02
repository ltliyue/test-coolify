# f22-pdf-reports 设计文档

> 版本：v1.0 | 日期：2026-04-02

## 架构概览

```
ReportScheduleConfig (PG, per-client 调度配置)
       ↓ Celery beat（定时检查到期的调度）
ReportGenerationService
  ├── CampaignQueryService（从仓库取数据，复用 f19）
  ├── HTMLTemplateRenderer（Jinja2 模板 → HTML）
  ├── PDFGenerator（weasyprint: HTML → PDF）
  ├── MinIO upload（PDF → 对象存储）
  └── EmailSender（SMTP: 发送带下载链接的邮件）
       ↓
ReportHistory (PG, 生成记录)
```

## 目录结构

### 新建文件

| 文件 | 说明 |
|------|------|
| `backend/app/models/report.py` | ReportSchedule + ReportHistory ORM |
| `backend/app/schemas/report.py` | Pydantic schemas |
| `backend/app/api/v1/reports.py` | API 路由（7 端点） |
| `backend/app/services/reports/__init__.py` | |
| `backend/app/services/reports/generator.py` | PDF 生成服务（数据获取+模板渲染+PDF转换） |
| `backend/app/services/reports/email_sender.py` | SMTP 邮件发送 |
| `backend/app/services/reports/templates/report_default.html` | 默认 Jinja2 报告模板 |
| `backend/app/tasks/report_tasks.py` | Celery 定时任务 |
| `infra/migrations/018_reports.sql` | PG 迁移 |

### 修改文件

| 文件 | 变更 |
|------|------|
| `backend/app/api/v1/router.py` | 注册 reports_router |
| `backend/app/core/config.py` | 添加 SMTP 配置 |
| `backend/requirements.txt` | 添加 weasyprint + jinja2 |

## 数据模型

### PG: report_schedules

| 字段 | 类型 | 说明 | 数据分级 |
|------|------|------|----------|
| id | UUID PK | | L1 |
| agency_id | UUID FK → agencies | 租户隔离 | L1 |
| client_id | UUID FK → clients | nullable | L1 |
| schedule_name | String(255) | 调度名称 | L0 |
| frequency | Enum | daily/weekly/monthly | L0 |
| recipients | JSON | 邮箱列表 `["a@b.com"]` | L1（业务邮箱，非终端用户 PII） |
| metrics_config | JSON | 包含的指标范围 | L0 |
| brand_config_override | JSON | 覆盖客户品牌配置（nullable） | L0 |
| is_active | Boolean | 默认 true | L0 |
| last_sent_at | DateTime(tz) | nullable | L1 |
| next_run_at | DateTime(tz) | nullable | L1 |
| created_at / updated_at | DateTime(tz) | | L1 |

### PG: report_history

| 字段 | 类型 | 说明 | 数据分级 |
|------|------|------|----------|
| id | UUID PK | | L1 |
| agency_id | UUID FK → agencies | 租户隔离 | L1 |
| schedule_id | UUID FK → report_schedules | nullable（手动触发时为 null） | L1 |
| client_id | UUID FK → clients | nullable | L1 |
| report_type | String(50) | campaign_performance / attribution | L0 |
| file_path | String(500) | MinIO 对象路径 | L1 |
| file_size_bytes | Integer | | L0 |
| recipients_count | Integer | 接收人数量（不存明文邮箱） | L0 |
| status | Enum | pending/generating/uploading/sending/success/failed | L0 |
| error_message | Text | 脱敏后的错误（仅异常类型名） | L1 |
| created_at | DateTime(tz) | | L1 |
| completed_at | DateTime(tz) | nullable | L1 |

## API 设计

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/reports/schedules` | 列出调度配置 |
| POST | `/reports/schedules` | 创建调度 |
| PUT | `/reports/schedules/{id}` | 更新调度 |
| DELETE | `/reports/schedules/{id}` | 删除调度 |
| POST | `/reports/generate` | 手动触发一次性报告 |
| GET | `/reports/history` | 报告历史列表 |
| GET | `/reports/history/{id}/download` | 获取 presigned URL |

## 关键逻辑

### ReportGenerationService

```python
async def generate_report(db, agency_id, client_id, metrics_config, brand_config):
    # 1. 从仓库查询 campaign 聚合数据（复用 CampaignQueryService）
    # 2. 加载 Jinja2 HTML 模板，注入数据 + 品牌配置
    # 3. weasyprint 将 HTML 转为 PDF bytes
    # 4. 上传 PDF 到 MinIO（路径: reports/{agency_id}/{date}/{uuid}.pdf）
    # 5. 创建 ReportHistory 记录
    # 6. 返回 (history_id, file_path)
```

### EmailSender

```python
class EmailSender:
    def __init__(self):
        # SMTP 配置从环境变量读取（合规规则 10：不硬编码凭证）
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        ...

    async def send_report_email(self, recipients, subject, download_url, agency_name):
        # 发送带 presigned URL 的邮件
        # URL 24小时有效（合规：报告文件过期机制）
        # Mock 模式：SMTP_HOST 为空时仅记录日志不实际发送
```

### Celery Beat Task

```python
@celery_app.task
def check_report_schedules():
    # 每小时检查一次
    # 查询 next_run_at <= now() 且 is_active 的 schedule
    # 对每个到期的 schedule: generate → upload → email → 更新 next_run_at
```

## 安全 & 合规考量

- **数据分级**：报告内容仅含 Level 0 聚合数据（spend/impressions/conversions），无 PII/PHI
- **审计日志**（规则 #12）：所有端点调用 audit_simple()，报告生成/发送也记录审计
- **租户隔离**（规则 #11）：所有查询 + MinIO 路径通过 agency_id 隔离
- **凭证安全**：SMTP 密码从环境变量读取，不日志记录
- **错误脱敏**（V-08）：error_message 仅保留异常类型名
- **文件过期**：presigned URL 24h 有效，MinIO 可配置 lifecycle policy
- **recipients 存储**：存在 schedule 的 JSON 中（L1 业务邮箱），report_history 仅存 count

## 错误处理

| 场景 | 处理 |
|------|------|
| 仓库无数据 | 生成空报告 + warning |
| weasyprint 渲染失败 | status=failed，记录异常类型 |
| MinIO 不可用 | status=failed，PDF 未上传 |
| SMTP 发送失败 | 重试 2 次，最终 failed |
| 调度频率无效 | 400 |
