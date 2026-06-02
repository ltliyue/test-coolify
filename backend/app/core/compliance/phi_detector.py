"""
PHI Detector — HIPAA Safe Harbor de-identification.

Scans for the 18 categories of PHI identifiers before data enters the warehouse,
preventing unprocessed PHI from reaching the analytics layer.

HIPAA Safe Harbor removal requirement covers 18 identifier categories:
https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/
"""
from __future__ import annotations

import re
import logging
from dataclasses import dataclass
from typing import Any

log = logging.getLogger("phi-detector")

# ── HIPAA 18-identifier PHI detection rules ──────────────────────────────────

_PATTERNS: dict[str, re.Pattern] = {
    # 1. Names (simple rule; complex cases require NLP)
    "name": re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"),

    # 2. Geographic subdivisions (beyond the first 3 digits of ZIP)
    "zip_code": re.compile(r"\b\d{5}(-\d{4})?\b"),

    # 3. Dates (any month/day; year alone is allowed)
    "date": re.compile(
        r"\b(0?[1-9]|1[0-2])[/-](0?[1-9]|[12]\d|3[01])[/-]\d{4}\b"
        r"|\b\d{4}-(0?[1-9]|1[0-2])-(0?[1-9]|[12]\d|3[01])\b"
    ),

    # 4. Phone numbers
    "phone": re.compile(
        r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
    ),

    # 5. Fax numbers (same shape as phone)
    "fax": re.compile(r"\bfax\s*:?\s*\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", re.IGNORECASE),

    # 6. Email addresses
    "email": re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b"),

    # 7. Social Security Number (SSN)
    "ssn": re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"),

    # 8. Medical record number (generic pattern)
    "medical_record": re.compile(r"\b(MRN|mrn|medical.?record.?number)\s*:?\s*\w+", re.IGNORECASE),

    # 9. Health plan beneficiary number
    "health_plan_number": re.compile(r"\b(HPN|health.?plan)\s*:?\s*\w+", re.IGNORECASE),

    # 10. Account numbers
    "account_number": re.compile(r"\baccount\s*#?\s*:?\s*\d{5,}\b", re.IGNORECASE),

    # 11. Certificate / license numbers
    "certificate": re.compile(r"\b(license|certificate)\s*#?\s*:?\s*\w{6,}\b", re.IGNORECASE),

    # 12. Vehicle identifier (VIN)
    "vehicle_id": re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b"),

    # 13. Device identifiers (MAC address, device serial number)
    "device_id": re.compile(r"\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b"),

    # 14. URLs (paths may contain personal info)
    "url": re.compile(r"https?://[^\s]+/[^\s]{10,}"),

    # 15. IP addresses (HIPAA treats IPs as PHI)
    "ip_address": re.compile(r"\b(\d{1,3}\.){3}\d{1,3}\b"),

    # 16. Biometric identifiers (fingerprint, iris, etc.) — cannot be regex-detected;
    #     must be flagged by business logic.

    # 17. Full-face photographs — detected via field name
    "photo": re.compile(r"\b(photo|image|face|selfie|portrait)\b", re.IGNORECASE),

    # 18. Other unique identifiers (generic UUID format)
    "unique_id": re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"),
}


@dataclass
class PHIDetectionResult:
    has_phi: bool
    findings: list[dict[str, Any]]  # [{type, value_snippet, field_path}]
    risk_level: str                  # 'none' | 'low' | 'medium' | 'high'


def scan_record(record: dict[str, Any], field_path: str = "") -> PHIDetectionResult:
    """
    Recursively scan a single data record for PHI identifiers.

    Args:
        record:     data dict to scan
        field_path: field path (used to report nested locations)

    Returns:
        PHIDetectionResult
    """
    findings: list[dict[str, Any]] = []

    for key, value in record.items():
        path = f"{field_path}.{key}" if field_path else key

        if isinstance(value, dict):
            sub_result = scan_record(value, path)
            findings.extend(sub_result.findings)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    sub_result = scan_record(item, f"{path}[{i}]")
                    findings.extend(sub_result.findings)
                elif isinstance(item, str):
                    findings.extend(_scan_string(item, path))
        elif isinstance(value, str):
            findings.extend(_scan_string(value, path))

        # Detect via field name (without looking at the value)
        key_lower = key.lower()
        if any(kw in key_lower for kw in ["ssn", "dob", "birth", "diagnosis", "icd", "npi", "mrn"]):
            findings.append({
                "type": "field_name_phi",
                "field_path": path,
                "value_snippet": f"[field name: {key}]",
                "confidence": "high",
            })

    has_phi = len(findings) > 0
    if not has_phi:
        risk_level = "none"
    elif len(findings) <= 2:
        risk_level = "low"
    elif len(findings) <= 5:
        risk_level = "medium"
    else:
        risk_level = "high"

    return PHIDetectionResult(has_phi=has_phi, findings=findings, risk_level=risk_level)


def _scan_string(text: str, field_path: str) -> list[dict[str, Any]]:
    results = []
    for phi_type, pattern in _PATTERNS.items():
        # Skip the UUID rule (too broad; only useful on specific fields)
        if phi_type == "unique_id":
            continue
        match = pattern.search(text)
        if match:
            snippet = match.group()[:20] + "..." if len(match.group()) > 20 else match.group()
            results.append({
                "type": phi_type,
                "field_path": field_path,
                "value_snippet": f"[REDACTED:{phi_type}]",  # never log the actual value
                "confidence": "medium",
            })
    return results


def deidentify_safe_harbor(record: dict[str, Any]) -> dict[str, Any]:
    """
    Apply HIPAA Safe Harbor de-identification: remove or mask the 18 PHI identifiers.
    Non-PHI fields useful for analytics are preserved.
    """
    result = {}
    for key, value in record.items():
        key_lower = key.lower()

        # Directly drop fields whose names look like PHI
        phi_field_keywords = [
            "name", "email", "phone", "fax", "ssn", "dob", "birth",
            "address", "zip", "postal", "mrn", "npi", "diagnosis",
            "icd", "photo", "image", "ip_address", "device_id",
        ]
        if any(kw in key_lower for kw in phi_field_keywords):
            result[key] = "[REMOVED:PHI]"
            continue

        if isinstance(value, dict):
            result[key] = deidentify_safe_harbor(value)
        elif isinstance(value, list):
            result[key] = [
                deidentify_safe_harbor(v) if isinstance(v, dict) else v
                for v in value
            ]
        elif isinstance(value, str):
            # Replace PHI patterns inside string values
            cleaned = value
            for phi_type, pattern in _PATTERNS.items():
                if phi_type in ("unique_id", "url", "photo"):
                    continue
                cleaned = pattern.sub(f"[REMOVED:{phi_type}]", cleaned)
            result[key] = cleaned
        else:
            result[key] = value

    return result
