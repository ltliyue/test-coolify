from __future__ import annotations
"""ETL Runner — executecomplete  extract→transform→load flow。"""
import logging
from typing import Optional

from app.services.etl.base import BaseAdapter, ETLresult
from app.core.warehouse_client import WarehouseClient
from app.core.compliance.phi_detector import scan_record
from app.core.compliance.anonymizer import anonymize_record_for_warehouse

log = logging.getLogger(__name__)


class ETLRunner:
    def __init__(self, warehouse: WarehouseClient):
        self.warehouse = warehouse

    def run(
        self,
        adapter: BaseAdapter,
        start_date: str,
        end_date: str,
        integration_id: str,
        cursor: Optional[str] = None,
    ) -> ETLresult:
        result = ETLresult(platform=adapter.platform)

        try:
            # 1. Extract
            log.info("ETL[%s] fetching %s → %s", adapter.platform, start_date, end_date)
            records, next_cursor = adapter.fetch(start_date, end_date, cursor)
            result.records_fetched = len(records)
            result.last_cursor = next_cursor

            # 2. Transform + Compliance
            clean_records = []
            for raw in records:
                # Compliance: unconditionally anonymize every record entering the warehouse (C-2 fix)
                phi_result = scan_record(raw)
                if phi_result.has_phi:
                    log.warning("ETL[%s] PHI detected in record — fields: %s", adapter.platform, phi_result.detected_fields if hasattr(phi_result, 'detected_fields') else 'unknown')
                raw = anonymize_record_for_warehouse(raw, adapter.agency_id)

                # Adapter-specific transformation
                transformed = adapter.transform(raw)
                if transformed is None:
                    result.records_skipped += 1
                    continue

                # inject agency context
                transformed["agency_id"] = adapter.agency_id
                transformed["client_id"] = adapter.client_id
                clean_records.append(transformed)

            # 3. Load
            if clean_records:
                written = self.warehouse.insert_many(adapter.get_raw_table(), clean_records)
                result.records_written = written

            # 4. Update sync state
            self.warehouse.update_sync_state(
                adapter.agency_id,
                integration_id,
                adapter.platform,
                next_cursor,
                result.records_written,
            )

            log.info(
                "ETL[%s] done: fetched=%d written=%d skipped=%d",
                adapter.platform,
                result.records_fetched,
                result.records_written,
                result.records_skipped,
            )
        except Exception as e:
            log.error("ETL[%s] failed: %s", adapter.platform, e, exc_info=True)
            result.errors.append(str(e))

        return result
