from __future__ import annotations
"""ETL adapterbase class。"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import logging

log = logging.getLogger(__name__)


@dataclass
class ETLresult:
    platform: str
    records_fetched: int = 0
    records_written: int = 0
    records_skipped: int = 0
    errors: list = field(default_factory=list)
    last_cursor: Optional[str] = None

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


class BaseAdapter(ABC):
    """all platformadapter base class。"""
    platform: str = ""

    def __init__(self, credentials: dict, agency_id: str, client_id: Optional[str] = None):
        self.credentials = credentials
        self.agency_id = agency_id
        self.client_id = client_id

    @abstractmethod
    def fetch(
        self, start_date: str, end_date: str, cursor: Optional[str] = None
    ) -> tuple[list[dict], Optional[str]]:
        """
        fetch data。
        return (records, next_cursor)
        records is rawdata dict list
        next_cursor is the pagination cursor (None indicates no more data)
        """

    @abstractmethod
    def get_raw_table(self) -> str:
        """Return the target raw table name, e.g. 'raw_ga4_events'."""

    def transform(self, record: dict) -> Optional[dict]:
        """
        Transform a single raw record into the warehouse format.
        Returns the raw record by default (subclasses may override).
        Returning None means skip this record.
        """
        return record
