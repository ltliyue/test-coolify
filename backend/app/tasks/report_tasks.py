from __future__ import annotations
"""Report-generation Celery tasks."""
import logging
import asyncio
from datetime import datetime, timezone, timedelta

from app.worker import celery_app

log = logging.getLogger(__name__)


@celery_app.task(name="tasks.generate_report", bind=True, max_retries=2)
def generate_report_task(self, history_id: str, agency_id: str):
    """Generate one report asynchronously (PDF → MinIO → email)."""
    from app.core.database import async_session
    from app.models.report import ReportHistory, ReportSchedule
    from app.services.reports.generator import generate_report_data, render_report_html, html_to_pdf, upload_report_to_storage
    from app.services.reports.email_sender import send_report_email
    from app.core.storage import get_presigned_url
    from sqlalchemy import select

    async def _run():
        async with async_session() as db:
            result = await db.execute(
                select(ReportHistory).where(ReportHistory.id == history_id, ReportHistory.agency_id == agency_id)
            )
            history = result.scalar_one_or_none()
            if not history:
                return "not_found"

            history.status = "generating"
            await db.commit()

            try:
                # 1. Fetch data
                campaigns, summary = generate_report_data(str(agency_id), str(history.client_id) if history.client_id else None, None, None)

                # 2. Render HTML → PDF
                html = render_report_html("ReceptivIQ", None, campaigns, summary, "Last 30 days", "Today")
                pdf_bytes = html_to_pdf(html)

                # 3. Upload to MinIO
                history.status = "uploading"
                await db.commit()
                file_path, file_size = upload_report_to_storage(pdf_bytes, str(agency_id))
                history.file_path = file_path
                history.file_size_bytes = file_size

                # 4. Send email (if linked to a schedule)
                if history.schedule_id:
                    sched_result = await db.execute(
                        select(ReportSchedule).where(
                            ReportSchedule.id == history.schedule_id,
                            ReportSchedule.agency_id == history.agency_id,  # Compliance rule 10: tenant isolation
                        )
                    )
                    schedule = sched_result.scalar_one_or_none()
                    if schedule and schedule.recipients_encrypted:
                        history.status = "sending"
                        await db.commit()
                        # Compliance rule 7: decrypt recipients
                        from app.core.encryption import decrypt_credentials
                        try:
                            decrypted = decrypt_credentials(schedule.recipients_encrypted)
                            recipients = decrypted.get("emails", [])
                        except Exception:
                            recipients = []
                        history.recipients_count = len(recipients)
                        if file_path and recipients:
                            url = get_presigned_url(file_path.split("/", 1)[-1] if "/" in file_path else file_path, expires_hours=24)
                            await send_report_email(recipients, f"Campaign Report — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}", url or "", "ReceptivIQ")

                history.status = "success"
                history.completed_at = datetime.now(timezone.utc)
                await db.commit()

                # Audit record
                from app.models.audit_log import AuditLog
                audit = AuditLog(
                    agency_id=history.agency_id,
                    action="report.generated",
                    resource_type="report_history",
                    resource_id=str(history.id),
                    success=True,
                    extra_data={"recipients_count": history.recipients_count, "file_size": file_size},
                    created_at=datetime.now(timezone.utc),
                )
                db.add(audit)
                await db.commit()
                return "success"

            except Exception as e:
                log.error("Report generation failed: %s", type(e).__name__)
                history.status = "failed"
                history.error_message = f"{type(e).__name__}: report generation failed"
                history.completed_at = datetime.now(timezone.utc)
                await db.commit()
                return "failed"

    return asyncio.run(_run())


@celery_app.task(name="tasks.check_report_schedules")
def check_report_schedules_task():
    """Hourly check for due report schedules."""
    from app.core.database import async_session
    from app.models.report import ReportSchedule, ReportHistory
    from sqlalchemy import select
    from datetime import timedelta

    async def _run():
        async with async_session() as db:
            now = datetime.now(timezone.utc)
            stmt = select(ReportSchedule).where(
                ReportSchedule.is_active == True,  # noqa: E712
                ReportSchedule.next_run_at <= now,
            )
            result = await db.execute(stmt)
            schedules = result.scalars().all()

            triggered = 0
            for sched in schedules:
                history = ReportHistory(
                    agency_id=sched.agency_id,
                    schedule_id=sched.id,
                    client_id=sched.client_id,
                    report_type="campaign_performance",
                    status="pending",
                )
                db.add(history)
                await db.flush()
                await db.refresh(history)

                # Update next_run_at
                if sched.frequency == "daily":
                    sched.next_run_at = now + timedelta(days=1)
                elif sched.frequency == "weekly":
                    sched.next_run_at = now + timedelta(weeks=1)
                elif sched.frequency == "monthly":
                    sched.next_run_at = now + timedelta(days=30)
                sched.last_sent_at = now

                await db.commit()

                # Trigger async generation
                generate_report_task.delay(str(history.id), str(sched.agency_id))
                triggered += 1

            # Compliance rule 11: system-task audit record
            if schedules:
                from app.models.audit_log import AuditLog
                audit = AuditLog(
                    action="report_schedule.triggered",
                    resource_type="system_task",
                    resource_id="celery_report_scheduler",
                    success=True,
                    extra_data={"schedules_checked": len(schedules), "triggered": triggered},
                    created_at=now,
                )
                db.add(audit)
                await db.commit()

            log.info("Report scheduler: checked %d schedules, triggered %d", len(schedules), triggered)
            return triggered

    return asyncio.run(_run())
