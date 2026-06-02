from __future__ import annotations
"""PDF reportgenerateservice — dataquery + template rendering + PDF convert + MinIO upload。

Compliance requirements:
- Report content only contains Level 0 aggregate data (no PII/PHI)
- File path includes agency_id (tenant isolation)
- Error info retains only the exception type name
"""
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from app.core.warehouse_client import get_warehouse
from app.services.campaign_query import CampaignQueryService

log = logging.getLogger(__name__)

# template directory
_TEMPLATE_DIR = Path(__file__).parent / "templates"
_jinja_env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=True)


def render_report_html(
    agency_name: str,
    brand_color: Optional[str],
    campaigns: list[dict],
    summary: dict,
    date_from: str,
    date_to: str,
) -> str:
    """render HTML report（only Level 0 aggregate data）。"""
    template = _jinja_env.get_template("report_default.html")
    now = datetime.now(timezone.utc)
    return template.render(
        agency_name=agency_name,
        brand_color=brand_color or "#2E75B6",
        campaigns=campaigns,
        total_spend=summary.get("total_spend", 0),
        total_impressions=summary.get("total_impressions", 0),
        total_clicks=summary.get("total_clicks", 0),
        total_conversions=summary.get("total_conversions", 0),
        date_range_from=date_from,
        date_range_to=date_to,
        generated_at=now.strftime("%Y-%m-%d %H:%M UTC"),
        generated_year=now.year,
    )


def html_to_pdf(html_content: str) -> bytes:
    """convert HTML convertto  PDF bytes。weasyprint unavailable when return HTML bytes as fallback。"""
    try:
        from weasyprint import HTML
        return HTML(string=html_content).write_pdf()
    except ImportError:
        log.warning("weasyprint not installed, returning HTML as fallback")
        return html_content.encode("utf-8")
    except Exception as e:
        log.error("PDF generation failed: %s", type(e).__name__)
        raise


def generate_report_data(agency_id: str, client_id: Optional[str], date_from: Optional[str], date_to: Optional[str]) -> tuple[list[dict], dict]:
    """from warehousegetreportdata（Level 0 aggregate data）。"""
    try:
        wh = get_warehouse()
        svc = CampaignQueryService(wh)
        campaigns = svc.list_campaigns(agency_id, client_id=client_id, date_from=date_from, date_to=date_to, limit=100)
        summary = svc.get_summary(agency_id, client_id=client_id, date_from=date_from, date_to=date_to)
        return campaigns, summary
    except Exception as e:
        log.warning("Warehouse data unavailable for report: %s", type(e).__name__)
        return [], {"total_spend": 0, "total_impressions": 0, "total_clicks": 0, "total_conversions": 0}


def upload_report_to_storage(pdf_bytes: bytes, agency_id: str) -> tuple[Optional[str], int]:
    """Upload PDF to MinIO; returns (file_path, file_size)."""
    from app.core.storage import upload_file
    now = datetime.now(timezone.utc)
    object_name = f"reports/{agency_id}/{now.strftime('%Y-%m-%d')}/{uuid.uuid4().hex[:12]}.pdf"
    path = upload_file(object_name, pdf_bytes, content_type="application/pdf")
    return path, len(pdf_bytes)
