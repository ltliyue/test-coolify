from __future__ import annotations
"""Budget-pacing Celery scheduled task — runs every 30 minutes."""
import logging
import asyncio

from app.worker import celery_app

log = logging.getLogger(__name__)


@celery_app.task(name="tasks.check_budget_pacing")
def check_budget_pacing_task():
    """Celery task wrapper — invokes the async budget-pacing check."""
    from app.core.database import async_session
    from app.core.warehouse_client import get_warehouse
    from app.services.campaign_query import CampaignQueryService
    from app.services.budget_pacing import check_budget_pacing

    async def _run():
        query_service = CampaignQueryService(get_warehouse())
        async with async_session() as db:
            alerts = await check_budget_pacing(db, query_service)
            log.info("Budget pacing check complete: %d alerts generated", len(alerts))
            return len(alerts)

    return asyncio.run(_run())
