"""Shared typed data contracts for DDCSE modules."""

from __future__ import annotations

from typing import Any, Literal, TypedDict


Operator = Literal[
    "less_than_or_equal",
    "less_than",
    "greater_than_or_equal",
    "greater_than",
]


class CovenantRuleConfig(TypedDict):
    """Structured covenant rule emitted by ingestion and consumed by compiler."""

    relation: str
    operator: Operator
    governors: str
    objects: str
    source_text: str


class FinancialPayload(TypedDict):
    """Standardized financial statement payload used by the UI and analytics."""

    ticker: str
    source: str
    period: str | None
    currency: str | None
    units: str
    scale_factor: float
    total_debt: float | None
    cash: float | None
    ebitda: float | None
    net_debt: float | None
    lineage: dict[str, str | None]
    errors: list[str]


class AuditRecord(TypedDict):
    """Serializable compliance decision record for audit export."""

    ticker: str
    covenant_type: str
    timestamp_utc: str
    total_debt: float
    cash: float
    ebitda: float
    ratio: float | str
    threshold: float
    compliant: bool
    buffer_distance: float | str
    warning_band: float
    source_payload: dict[str, Any]
