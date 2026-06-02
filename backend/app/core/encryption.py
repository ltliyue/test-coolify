from __future__ import annotations
"""
Fernet-based field-level encryption for the Credential Vault.
Each tenant's OAuth tokens and API keys are encrypted with the shared ENCRYPTION_KEY.
For production, consider per-tenant key derivation (HKDF) from a master key.
"""
import json
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


@lru_cache(maxsize=1)
def _get_fernet() -> Fernet:
    key = settings.ENCRYPTION_KEY
    if not key:
        raise RuntimeError(
            "ENCRYPTION_KEY is not configured. "
            "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
    try:
        return Fernet(key.encode())
    except Exception:
        raise RuntimeError("Invalid ENCRYPTION_KEY format")  # H-09: do not leak key fragments


def encrypt_credentials(data: dict) -> str:
    """Serialize dict to JSON, then Fernet-encrypt. Returns ciphertext string."""
    plaintext = json.dumps(data).encode()
    return _get_fernet().encrypt(plaintext).decode()


def decrypt_credentials(encrypted: str) -> dict:
    """Fernet-decrypt ciphertext string and deserialize to dict."""
    try:
        plaintext = _get_fernet().decrypt(encrypted.encode()).decode()
        return json.loads(plaintext)
    except (InvalidToken, json.JSONDecodeError) as e:
        raise ValueError(f"Failed to decrypt credentials: {e}")


def mask_credentials(data: dict) -> dict:
    """Mask sensitive values for display — never log raw secrets."""
    masked = {}
    for k, v in data.items():
        s = str(v)
        masked[k] = f"***{s[-4:]}" if len(s) > 4 else "***"
    return masked
