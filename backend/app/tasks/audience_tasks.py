from __future__ import annotations
"""Audience-export Celery tasks — async platform audience creation."""
import logging
import asyncio

from app.worker import celery_app

log = logging.getLogger(__name__)


@celery_app.task(name="tasks.execute_audience_export", bind=True, max_retries=1)
def execute_audience_export_task(self, export_id: str, agency_id: str):
    """Celery task: async persona → platform audience export."""
    from app.core.database import async_session
    from app.services.audience_export.service import execute_export

    async def _run():
        async with async_session() as db:
            export = await execute_export(db, export_id, agency_id)
            if export.status == "pending" and export.retry_count <= 1:
                # Retry
                log.info("Retrying audience export %s (attempt %d)", export_id, export.retry_count)
                export = await execute_export(db, export_id, agency_id)
            return export.status

    return asyncio.run(_run())
