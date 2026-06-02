"""
Anonymizer — pseudonymization / anonymization utilities
Run before PII/PHI is written to the warehouse (Snowflake).

GDPR distinction:
  Pseudonymization: reversible, requires separately stored mapping (still GDPR-scoped)
  Anonymization: irreversible, outside GDPR scope

This module defaults to irreversible one-way hashing (anonymization);
use reversible pseudonymization only when business requires (extra authorization needed).
"""
from __future__ import annotations

import hashlib
import ipaddress
import re
import logging
from typing import Any

log = logging.getLogger("anonymizer")


def hash_identifier(value: str, salt: str) -> str:
    """
    One-way hash a user identifier (email, user_id, etc.).
    Uses SHA-256 + tenant-level salt to guarantee:
    1. Same email across tenants produces different hashes (prevents cross-tenant linkage)
    2. Hash is irreversible (cannot recover original)
    3. Within one tenant, joinable across tables (session → conversion)

    Args:
        value: raw identifier (email, phone, etc.)
        salt:  tenant-specific salt (agency_id or dedicated random salt)

    Returns:
        64-char hex hash string
    """
    if not value or not salt:
        return ""
    normalized = value.strip().lower()
    combined = f"{salt}:{normalized}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def truncate_ip(ip_str: str, level: int = 3) -> str:
    """
    Truncate IP address to lower precision (required by GDPR + HIPAA).

    Args:
        ip_str: raw IP (IPv4 or IPv6)
        level:  bytes to keep (IPv4: 1-4, default 3 i.e. 192.168.1.x → 192.168.1.0)

    Returns:
        truncated IP string with last octet zeroed
    """
    if not ip_str:
        return ""
    try:
        addr = ipaddress.ip_address(ip_str.strip())
        if addr.version == 4:
            parts = str(addr).split(".")
            masked = parts[:level] + ["0"] * (4 - level)
            return ".".join(masked)
        else:
            # IPv6: keep first 48 bits (/48 prefix), zero out the rest
            network = ipaddress.ip_network(f"{addr}/48", strict=False)
            return str(network.network_address)
    except ValueError:
        log.warning("Invalid IP address for truncation: %s", ip_str)
        return ""


def mask_email(email: str) -> str:
    """
    Partially mask email address for log display (not for storage).
    example: user@example.com → u***@e***.com
    """
    if not email or "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    domain_parts = domain.split(".")
    return f"{local[0]}***@{domain_parts[0][0]}***.{domain_parts[-1]}"


def anonymize_record_for_warehouse(
    record: dict[str, Any],
    tenant_salt: str,
    pii_fields: list[str] | None = None,
) -> dict[str, Any]:
    """
    Anonymize a single record before writing to the warehouse.
    Hash PII columns, truncate IP, pass other columns through unchanged.

    Args:
        record:      original record dict
        tenant_salt: tenant-specific salt
        pii_fields:  list of field names to hash (defaults to built-in list)

    Returns:
        anonymized record
    """
    DEFAULT_PII_FIELDS = {
        "email", "user_email", "customer_email",
        "phone", "telephone", "mobile",
        "user_id", "customer_id", "visitor_id", "client_id_external",
        "cookie_id", "device_id", "advertising_id",
        "name", "full_name", "first_name", "last_name",
    }
    fields_to_hash = set(pii_fields or []) | DEFAULT_PII_FIELDS

    result = {}
    for key, value in record.items():
        key_lower = key.lower()

        if key_lower in fields_to_hash and isinstance(value, str) and value:
            # hash PII column
            result[key] = hash_identifier(value, tenant_salt)

        elif "ip" in key_lower and isinstance(value, str):
            # truncate IP address
            result[key] = truncate_ip(value, level=3)

        elif isinstance(value, dict):
            result[key] = anonymize_record_for_warehouse(value, tenant_salt, pii_fields)

        else:
            result[key] = value

    return result


def scrub_pii_from_logs(message: str) -> str:
    """
    Strip common PII patterns from log messages (keep PII out of logging system).
    Intended for use in a logging handler.
    """
    patterns = [
        (re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b"), "[EMAIL]"),
        (re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"), "[SSN]"),
        (re.compile(r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[PHONE]"),
    ]
    result = message
    for pattern, replacement in patterns:
        result = pattern.sub(replacement, result)
    return result
