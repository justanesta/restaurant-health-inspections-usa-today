"""Extractor registry — maps a source key to its Extractor class."""

from __future__ import annotations

from ..config import SourceConfig
from .albuquerque import AlbuquerqueCityExtractor
from .base import ExtractResult, Extractor
from .los_angeles import LosAngelesCountyExtractor
from .new_york import NewYorkStateExtractor

_REGISTRY: dict[str, type[Extractor]] = {
    "new_york_state": NewYorkStateExtractor,
    "los_angeles_county": LosAngelesCountyExtractor,
    "albuquerque_city": AlbuquerqueCityExtractor,
}


def get_extractor(source: SourceConfig, cfg) -> Extractor:
    try:
        cls = _REGISTRY[source.key]
    except KeyError as exc:
        raise KeyError(f"No extractor registered for source {source.key!r}") from exc
    return cls(source, cfg)


__all__ = ["Extractor", "ExtractResult", "get_extractor"]
