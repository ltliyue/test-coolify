from __future__ import annotations
"""BudgetPacingService — check budget pacing deviation and trigger alerts."""
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import CampaignBudgetConfig
from app.models.notification import Notification
from app.services.campaign_query import CampaignQueryService

log = logging.getLogger(__name__)


async def check_budget_pacing(db: AsyncSession, query_service: CampaignQueryService):
    """Check all alert-enabled budget configs and create a notification when deviation exceeds the threshold."""
    stmt = select(CampaignBudgetConfig).where(
        CampaignBudgetConfig.alert_enabled == True,  # noqa: E712
        CampaignBudgetConfig.daily_budget.isnot(None),
    )
    result = await db.execute(stmt)
    configs = result.scalars().all()

    now = datetime.now(timezone.utc)
    hour_fraction = now.hour / 24.0
    if hour_fraction == 0:
        return []

    alerts = []
    for config in configs:
        try:
            actual_spend = query_service.get_campaign_spend_today(
                str(config.agency_id), config.platform, config.external_campaign_id
            )
            expected_spend = float(config.daily_budget) * hour_fraction
            if expected_spend == 0:
                continue

            deviation = (actual_spend - expected_spend) / expected_spend

            if abs(deviation) > config.pacing_alert_threshold:
                direction = "overspending" if deviation > 0 else "underspending"
                message = (
                    f"Campaign '{config.campaign_name or config.external_campaign_id}' "
                    f"on {config.platform} is {direction}: "
                    f"${actual_spend:.2f} vs expected ${expected_spend:.2f} "
                    f"({abs(deviation):.0%} deviation)"
                )

                notification = Notification(
                    agency_id=config.agency_id,
                    type="budget_alert",
                    title=f"Budget Pacing Alert: {config.campaign_name or config.external_campaign_id}",
                    message=message,
                    metadata={
                        "platform": config.platform,
                        "external_campaign_id": config.external_campaign_id,
                        "daily_budget": float(config.daily_budget),
                        "actual_spend": actual_spend,
                        "deviation_pct": round(deviation, 4),
                    },
                )
                db.add(notification)
                alerts.append(notification)
                log.info("Budget alert: %s", message)
        except Exception as e:
            log.error("Budget pacing check failed for config %s: %s", config.id, e)

    # V-06 compliance fix: add an audit record for the system scheduled task
    if alerts or configs:
        from app.models.audit_log import AuditLog
        audit_entry = AuditLog(
            action="budget_pacing.check",
            resource_type="system_task",
            resource_id="celery_budget_pacing",
            success=True,
            extra_data={"configs_checked": len(configs), "alerts_generated": len(alerts)},
            created_at=now,
        )
        db.add(audit_entry)
        await db.commit()
    return alerts
