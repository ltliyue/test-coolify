from __future__ import annotations
"""
M-02/M-03: encrypt/decrypt utilities for user PII fields.
email and full_name are Fernet-encrypted at rest; email_hash is used for lookup.
"""
import hashlib
import logging
from typing import Optional

log = logging.getLogger(__name__)

# Salt-hashing prefix (defense against rainbow tables)
_HASH_SALT = "receptiviq:pii:"


def hash_email(email: str) -> str:
    """Generate a deterministic SHA-256 hash of the email (used for lookup and UNIQUE constraint)."""
    normalized = email.strip().lower()
    return hashlib.sha256(f"{_HASH_SALT}{normalized}".encode()).hexdigest()


def encrypt_pii(value: str) -> str:
    """Fernet-encrypt a PII field value."""
    try:
        from app.core.encryption import _get_fernet
        return _get_fernet().encrypt(value.encode()).decode()
    except Exception:
        # Return the value unchanged when ENCRYPTION_KEY is unset (dev env)
        log.debug("PII encryption skipped (ENCRYPTION_KEY not configured)")
        return value


def decrypt_pii(value: str) -> str:
    """Fernet-decrypt a PII field value. Tolerates pre-encryption legacy data."""
    if not value:
        return value
    try:
        from app.core.encryption import _get_fernet
        return _get_fernet().decrypt(value.encode()).decode()
    except Exception:
        # Decryption failure means legacy unencrypted data — return as-is
        return value


def encrypt_user_fields(email: str, full_name: str) -> dict:
    """
    Encrypt user PII fields in one shot and return as a dict.
    Use when creating/updating a user.
    """
    return {
        "email": encrypt_pii(email),
        "email_hash": hash_email(email),
        "full_name": encrypt_pii(full_name),
    }
