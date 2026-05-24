"""Audit record generation for covenant compliance runs."""

from __future__ import annotations

from datetime import UTC, datetime
import json
import math
from typing import Any

from compiler import CompiledCovenant
from contracts import AuditRecord, FinancialPayload


def _json_safe_float(value: float) -> float | str:
    if math.isfinite(value):
        return value
    if value == math.inf:
        return "Infinity"
    return "-Infinity"


def build_audit_record(
    ticker: str,
    covenant: CompiledCovenant,
    total_debt: float,
    cash: float,
    ebitda: float,
    ratio: float,
    compliant: bool,
    buffer_distance: float,
    warning_band: float,
    source_payload: FinancialPayload | dict[str, Any],
    severity_score: float = 0.0,
    case_name: str | None = None,
) -> AuditRecord:
    """Build a serializable audit record for one compliance decision."""

    return {
        "ticker": ticker,
        "covenant_type": covenant.covenant_type,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "total_debt": total_debt,
        "cash": cash,
        "ebitda": ebitda,
        "ratio": _json_safe_float(ratio),
        "threshold": covenant.threshold,
        "compliant": compliant,
        "buffer_distance": _json_safe_float(buffer_distance),
        "warning_band": warning_band,
        "severity_score": round(severity_score, 1),
        "case_name": case_name,
        "source_payload": dict(source_payload),
    }


def audit_record_to_json(record: AuditRecord) -> str:
    """Serialize an audit record with stable formatting for export."""

    return json.dumps(record, indent=2, sort_keys=True)
