from __future__ import annotations
from pydantic import BaseModel


class ImportResponse(BaseModel):
    platform: str
    rows_imported: int
    rows_skipped: int
    message: str
