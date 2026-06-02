"""DSN fingerprint helper.

Logging, audit and Sentry messages must NEVER include the raw tenant
DSN (it contains credentials). This module exposes a single helper
that returns a stable 12-char SHA-256 prefix suitable for correlation
without leaking the secret.
"""
from __future__ import annotations

import hashlib


def dsn_fingerprint(dsn: str) -> str:
    """Return a stable 12-char SHA-256 prefix of the given DSN string."""
    if not dsn:
        return "<empty>"
    return hashlib.sha256(dsn.encode("utf-8")).hexdigest()[:12]


__all__ = ["dsn_fingerprint"]
