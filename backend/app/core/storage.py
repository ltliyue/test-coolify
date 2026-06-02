from __future__ import annotations
"""MinIO object-storage client — lazy singleton; silent degradation when unconfigured."""
import io
import logging
from typing import Optional

from app.core.config import settings

log = logging.getLogger(__name__)

_minio_client = None


def get_storage():
    """Get the MinIO client (lazy singleton; returns None when unconfigured)."""
    global _minio_client
    if _minio_client is not None:
        return _minio_client

    if not settings.MINIO_ENDPOINT or not settings.MINIO_ACCESS_KEY:
        log.info("MinIO not configured, storage disabled")
        return None

    try:
        from minio import Minio
        _minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
        if not _minio_client.bucket_exists(settings.MINIO_BUCKET):
            _minio_client.make_bucket(settings.MINIO_BUCKET)
            log.info("Created MinIO bucket: %s", settings.MINIO_BUCKET)
        return _minio_client
    except Exception as e:
        log.warning("MinIO init failed (storage disabled): %s", e)
        _minio_client = None
        return None


def upload_file(object_name: str, data: bytes, content_type: str = "application/octet-stream") -> Optional[str]:
    """Upload a file to MinIO and return the object path. Returns None if MinIO is unavailable."""
    client = get_storage()
    if client is None:
        return None
    try:
        client.put_object(
            settings.MINIO_BUCKET,
            object_name,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return f"{settings.MINIO_BUCKET}/{object_name}"
    except Exception as e:
        log.error("MinIO upload failed: %s", e)
        return None


def get_presigned_url(object_name: str, expires_hours: int = 1) -> Optional[str]:
    """Return a pre-signed download URL."""
    client = get_storage()
    if client is None:
        return None
    try:
        from datetime import timedelta
        return client.presigned_get_object(
            settings.MINIO_BUCKET, object_name, expires=timedelta(hours=expires_hours),
        )
    except Exception as e:
        log.error("MinIO presigned URL failed: %s", e)
        return None


def delete_file(object_name: str) -> bool:
    """Delete a file."""
    client = get_storage()
    if client is None:
        return False
    try:
        client.remove_object(settings.MINIO_BUCKET, object_name)
        return True
    except Exception as e:
        log.error("MinIO delete failed: %s", e)
        return False
