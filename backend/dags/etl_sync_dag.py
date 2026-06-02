"""
ReceptivIQ ETL Sync DAG — daily pull from each platform into the warehouse.
Schedule: daily at 06:00 UTC
Flow: GA4 / Meta Ads / HubSpot pulled in parallel → dbt transforms
"""
from __future__ import annotations
import os
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

# Ensure backend is on Python path (inside the Airflow container)
_backend_path = os.environ.get("BACKEND_PATH", "/opt/airflow/backend")
if _backend_path not in sys.path:
    sys.path.insert(0, _backend_path)

default_args = {
    "owner": "receptiviq",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def _sync_platform(platform: str, **context):
    """Invoke the ETL Runner to sync data for a given platform."""
    from app.services.etl.runner import ETLRunner
    from app.core.warehouse_client import get_warehouse

    agency_id = os.environ.get("DEFAULT_AGENCY_ID", "00000000-0000-0000-0000-000000000001")
    ds = context.get("ds", datetime.utcnow().strftime("%Y-%m-%d"))

    from app.services.etl.adapters.ga4 import GA4Adapter
    from app.services.etl.adapters.meta_ads import MetaAdsAdapter
    from app.services.etl.adapters.hubspot import HubSpotAdapter

    adapter_map = {"ga4": GA4Adapter, "meta_ads": MetaAdsAdapter, "hubspot": HubSpotAdapter}
    adapter_cls = adapter_map[platform]
    adapter = adapter_cls(credentials={"mock": True}, agency_id=agency_id)

    warehouse = get_warehouse()
    runner = ETLRunner(warehouse)
    result = runner.run(adapter, ds, ds, f"airflow-{platform}", None)
    print(f"ETL sync {platform}: fetched={result.records_fetched} written={result.records_written}")


def _run_dbt(**context):
    """Run dbt transforms."""
    import subprocess
    dbt_dir = os.path.join(os.path.dirname(_backend_path), "dbt")
    result = subprocess.run(
        ["dbt", "run", "--project-dir", dbt_dir, "--profiles-dir", dbt_dir],
        capture_output=True, text=True, timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(f"dbt run failed: {(result.stderr or '')[-500:]}")
    print(f"dbt run completed: {(result.stdout or '')[-300:]}")


with DAG(
    dag_id="receptiviq_etl_sync",
    default_args=default_args,
    description="Daily ETL: GA4 + Meta Ads + HubSpot → DuckDB/Snowflake → dbt",
    schedule_interval="0 6 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["etl", "receptiviq"],
) as dag:

    sync_ga4 = PythonOperator(
        task_id="sync_ga4",
        python_callable=_sync_platform,
        op_kwargs={"platform": "ga4"},
    )
    sync_meta = PythonOperator(
        task_id="sync_meta_ads",
        python_callable=_sync_platform,
        op_kwargs={"platform": "meta_ads"},
    )
    sync_hubspot = PythonOperator(
        task_id="sync_hubspot",
        python_callable=_sync_platform,
        op_kwargs={"platform": "hubspot"},
    )
    dbt_transform = PythonOperator(
        task_id="dbt_transform",
        python_callable=_run_dbt,
    )

    # Three platforms in parallel → dbt transforms
    [sync_ga4, sync_meta, sync_hubspot] >> dbt_transform
