"""SQLAlchemy TypeDecorator that transparently encrypts/decrypts a column.

Used by ``Agency.db_dsn`` / ``Agency.db_dsn_previous`` so the per-tenant
connection string never sits in plaintext at rest. Encryption uses the
project Fernet key wired through ``app.core.pii_crypto``.
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import String
from sqlalchemy.types import TypeDecorator


class EncryptedDSN(TypeDecorator):
    """Fernet-encrypts the value on bind, decrypts on load.

    ``cache_ok=True`` because the transformation is stateless and the
    column type itself does not carry per-instance state.
    """

    impl = String
    cache_ok = True

    def process_bind_param(
        self, value: Optional[str], dialect: Any
    ) -> Optional[str]:
        if value is None:
            return None
        from app.core.pii_crypto import encrypt_pii

        return encrypt_pii(value)

    def process_result_value(
        self, value: Optional[str], dialect: Any
    ) -> Optional[str]:
        if value is None:
            return None
        from app.core.pii_crypto import decrypt_pii

        return decrypt_pii(value)


__all__ = ["EncryptedDSN"]
