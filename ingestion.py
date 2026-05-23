"""Ingestion primitives for Dynamic Debt Covenant Surveillance Engine.

The module models credit agreement language as structured contract terms. It
intentionally avoids executable strings so downstream compilers can consume a
typed dictionary representation instead of unsafe raw evaluation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import logging
import re
from typing import Any, Iterable

from contracts import CovenantRuleConfig


logger = logging.getLogger(__name__)


ARTICLE_VI_MOCK_CHUNKS: tuple[str, ...] = (
    (
        "ARTICLE VI - Negative Covenants. Section 6.01 Financial Covenant. "
        "The Borrower shall not permit the Consolidated Net Leverage Ratio "
        "as of the last day of any Fiscal Quarter to exceed 3.50 to 1.00."
    ),
    (
        "Section 6.02 Limitation on Indebtedness. The Borrower shall not "
        "create, incur, assume or suffer to exist any Indebtedness except "
        "as otherwise permitted under this Agreement."
    ),
    (
        "Section 6.03 Minimum Interest Coverage Ratio. The Borrower shall "
        "maintain a Consolidated Interest Coverage Ratio greater than 2.00 "
        "to 1.00 as of the last day of each Test Period."
    ),
    (
        "Section 6.04 Fixed Charge Coverage Ratio. The Borrower shall "
        "maintain a Fixed Charge Coverage Ratio of at least 1.25 to 1.00."
    ),
    (
        "Section 6.05 Minimum Liquidity. The Borrower shall maintain Minimum "
        "Liquidity greater than 50.00 at all times."
    ),
)


@dataclass(frozen=True, slots=True)
class CovenantTerm:
    """Structured representation of a parsed financial covenant clause."""

    relation: str
    operator: str
    governors: str
    objects: str
    source_text: str

    def to_dict(self) -> dict[str, str]:
        """Return a serializable dictionary for compiler handoff."""

        return asdict(self)


_RELATION_PATTERNS: tuple[tuple[str, str, str], ...] = (
    (r"shall\s+not\s+permit.*?to\s+exceed", "not to exceed", "less_than_or_equal"),
    (r"not\s+to\s+exceed", "not to exceed", "less_than_or_equal"),
    (r"greater\s+than", "greater than", "greater_than"),
    (r"less\s+than", "less than", "less_than"),
    (r"at\s+least", "at least", "greater_than_or_equal"),
)


def load_mock_article_vi_chunks() -> tuple[str, ...]:
    """Return PDF-like chunks from Article VI of a mock credit agreement."""

    logger.info("Loaded %s mock Article VI covenant chunks", len(ARTICLE_VI_MOCK_CHUNKS))
    return ARTICLE_VI_MOCK_CHUNKS


def parse_covenant_chunk(chunk: str) -> CovenantTerm | None:
    """Parse a credit agreement chunk into relation/operator/governor/object fields."""

    normalized = " ".join(chunk.strip().split())
    if not normalized:
        logger.warning("Skipped empty covenant chunk")
        return None

    relation = ""
    operator = ""
    for pattern, relation_value, operator_value in _RELATION_PATTERNS:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            relation = relation_value
            operator = operator_value
            break

    governor_match = re.search(
        r"(Consolidated\s+[A-Za-z\s]+?Ratio)",
        normalized,
        flags=re.IGNORECASE,
    )
    object_match = re.search(
        r"(?:exceed|greater\s+than|less\s+than|at\s+least)\s+(\d+(?:\.\d+)?)\s*(?:to\s*1\.00|x)?",
        normalized,
        flags=re.IGNORECASE,
    )

    if not relation or not governor_match or not object_match:
        logger.info("Chunk did not contain a supported financial covenant: %s", normalized)
        return None

    term = CovenantTerm(
        relation=relation,
        operator=operator,
        governors=governor_match.group(1).strip(),
        objects=object_match.group(1),
        source_text=normalized,
    )
    logger.info("Parsed covenant term: %s", term)
    return term


def parse_article_vi_chunks(chunks: Iterable[str]) -> list[dict[str, str]]:
    """Parse Article VI chunks into structured dictionary configurations."""

    terms: list[dict[str, str]] = []
    for chunk in chunks:
        term = parse_covenant_chunk(chunk)
        if term is not None:
            terms.append(term.to_dict())
    logger.info("Parsed %s covenant terms from Article VI chunks", len(terms))
    return terms


def default_covenant_config() -> CovenantRuleConfig:
    """Return the canonical leverage covenant dictionary used by examples/tests."""

    return {
        "relation": "not to exceed",
        "operator": "less_than_or_equal",
        "governors": "Consolidated Net Leverage Ratio",
        "objects": "3.50",
        "source_text": ARTICLE_VI_MOCK_CHUNKS[0],
    }


def covenant_templates() -> dict[str, CovenantRuleConfig]:
    """Return supported covenant rule templates for UI and test scenarios."""

    return {
        "Net Leverage": default_covenant_config(),
        "Interest Coverage": {
            "relation": "greater than",
            "operator": "greater_than",
            "governors": "Consolidated Interest Coverage Ratio",
            "objects": "2.00",
            "source_text": ARTICLE_VI_MOCK_CHUNKS[2],
        },
        "Fixed Charge Coverage": {
            "relation": "at least",
            "operator": "greater_than_or_equal",
            "governors": "Fixed Charge Coverage Ratio",
            "objects": "1.25",
            "source_text": ARTICLE_VI_MOCK_CHUNKS[3],
        },
        "Minimum Liquidity": {
            "relation": "greater than",
            "operator": "greater_than",
            "governors": "Minimum Liquidity",
            "objects": "50.00",
            "source_text": ARTICLE_VI_MOCK_CHUNKS[4],
        },
    }
