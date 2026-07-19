"""Deterministic identifiers.

UUIDv5 (namespaced SHA-1) means the same natural key always yields the same UUID —
so re-running the pipeline produces identical ids and loads are idempotent (ADR 0007).
No database sequence or random component is involved.
"""

from __future__ import annotations

import uuid

# Project namespace. Stable forever — changing it re-mints every id.
_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://usatoday.example/restaurant-inspections")


def _uuid5(*parts: str) -> str:
    return str(uuid.uuid5(_NAMESPACE, "|".join(parts)))


def inspection_uuid(source: str, natural_key: str) -> str:
    """UUID for one inspection event. `natural_key` must be unique within `source`."""
    return _uuid5("inspection", source, natural_key)


def establishment_uuid(source: str, establishment_key: str) -> str:
    """UUID for one establishment. `establishment_key` = the source's facility/permit id."""
    return _uuid5("establishment", source, establishment_key)
