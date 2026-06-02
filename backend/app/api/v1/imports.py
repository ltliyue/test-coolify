from __future__ import annotations
"""F-14 historical data CSV import API."""
import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.import_schema import ImportResponse
from app.services.etl.historical_importer import detect_format, run_historical_import

router = APIRouter(prefix="/import", tags=["import"])

SUPPORTED_PLATFORMS = ("meta_ads", "ga4", "hubspot")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/upload", response_model=ImportResponse)
async def upload_historical_csv(
    file: UploadFile = File(..., description="CSV file (UTF-8 or UTF-8-BOM)"),
    platform: Optional[str] = Form(None, description="platform name: meta_ads / ga4 / hubspot (leave empty to auto-detect)"),
    client_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
) -> ImportResponse:
    """
    Upload a historical-data CSV file and import it into the data warehouse (DuckDB).

    - Supported: meta_ads / ga4 / hubspot
    - Auto-detects format when the platform parameter is empty
    - Max 50 MB
    """
    # file size check
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {MAX_FILE_SIZE // 1024 // 1024} MB",
        )

    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    # auto-detectformat
    if not platform:
        text = content.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text))
        headers = next(reader, [])
        platform = detect_format(headers)
        if not platform:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot detect platform format from CSV headers. Please specify 'platform' parameter.",
            )

    if platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported platform '{platform}'. Supported: {SUPPORTED_PLATFORMS}",
        )

    try:
        result = run_historical_import(
            content=content,
            platform=platform,
            agency_id=str(current_user.agency_id),
            client_id=client_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Import error: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Import processing failed")

    return ImportResponse(
        platform=result["platform"],
        rows_imported=result["rows_imported"],
        rows_skipped=result["rows_skipped"],
        message=f"Successfully imported {result['rows_imported']} rows from {platform}",
    )
