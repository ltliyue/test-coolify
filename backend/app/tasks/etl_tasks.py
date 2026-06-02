from __future__ import annotations
"""ETL Celery tasks — triggered by the Airflow DAG or via API /integrations/{id}/sync."""
import logging
import uuid

from app.worker import celery_app
from app.core.sync_database import get_sync_db
from app.core.warehouse_client import get_warehouse
from app.services.etl.runner import ETLRunner
from app.services.etl.adapters.ga4 import GA4Adapter
from app.services.etl.adapters.meta_ads import MetaAdsAdapter
from app.services.etl.adapters.hubspot import HubSpotAdapter
from app.models.integration import Integration
from app.models.credential import Credential
from app.core.encryption import decrypt_credentials

log = logging.getLogger(__name__)

ADAPTER_MAP = {
    "ga4": GA4Adapter,
    "meta_ads": MetaAdsAdapter,
    "hubspot": HubSpotAdapter,
}


@celery_app.task(bind=True, name="etl.sync", max_retries=3, default_retry_delay=60)
def run_etl_sync(self, integration_id: str, start_date: str, end_date: str) -> dict:
    """
    Synchronous function (callable from a Celery task or directly).
    Load Integration + Credential from DB, then run the matching ETL adapter.
    """
    with get_sync_db() as db:
        # Load integration config
        integration = db.get(Integration, uuid.UUID(integration_id))
        if not integration:
            raise ValueError(f"Integration {integration_id} not found")

        # Load credentials
        creds_dict: dict = {}
        if integration.credential_id:
            credential = db.get(Credential, integration.credential_id)
            if credential:
                creds_dict = decrypt_credentials(credential.encrypted_data)

        # Create adapter
        adapter_cls = ADAPTER_MAP.get(integration.platform.value)
        if not adapter_cls:
            raise ValueError(f"No ETL adapter for platform: {integration.platform.value}")

        adapter = adapter_cls(
            credentials=creds_dict,
            agency_id=str(integration.agency_id),
            client_id=str(integration.client_id) if integration.client_id else None,
        )

        # Fetch sync cursor
        warehouse = get_warehouse()
        state = warehouse.get_sync_state(str(integration.agency_id), integration_id)
        cursor = state.get("last_cursor") if state else None

        # Run ETL
        runner = ETLRunner(warehouse)
        result = runner.run(adapter, start_date, end_date, integration_id, cursor)

        return {
            "platform": result.platform,
            "records_fetched": result.records_fetched,
            "records_written": result.records_written,
            "records_skipped": result.records_skipped,
            "success": result.success,
            "errors": result.errors,
        }


@celery_app.task(name="etl.run_dbt")
def run_dbt_transform() -> dict:
    """Trigger dbt transforms (staging → canonical → marts)."""
    import subprocess
    try:
        result = subprocess.run(
            ["dbt", "run", "--project-dir", "/app/dbt", "--profiles-dir", "/app/dbt"],
            capture_output=True, text=True, timeout=300,
        )
        log.info("dbt run completed: returncode=%d", result.returncode)
        return {"status": "success" if result.returncode == 0 else "failed",
                "stdout": (result.stdout or "")[-500:],
                "stderr": (result.stderr or "")[-500:]}
    except Exception as e:
        log.error("dbt run error: %s", type(e).__name__)  # H-10: do not leak internal exception details
        return {"status": "error", "detail": "dbt transformation failed"}
