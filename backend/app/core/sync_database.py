from __future__ import annotations
"""
Synchronous SQLAlchemy session for Celery workers.
Celery tasks cannot use async sessions — use this instead of core/database.py.
"""
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

sync_engine = create_engine(settings.SYNC_DATABASE_URL, pool_pre_ping=True)
SyncSession = sessionmaker(bind=sync_engine, autoflush=False, autocommit=False)


@contextmanager
def get_sync_db() -> Session:
    db = SyncSession()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
