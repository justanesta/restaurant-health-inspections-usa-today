"""Transformer registry — maps a source key to its Transformer class."""

from __future__ import annotations

from ..config import SourceConfig
from .albuquerque import AlbuquerqueCityTransformer
from .base import Transformer
from .los_angeles import LosAngelesCountyTransformer
from .new_york import NewYorkStateTransformer

_REGISTRY: dict[str, type[Transformer]] = {
    "new_york_state": NewYorkStateTransformer,
    "los_angeles_county": LosAngelesCountyTransformer,
    "albuquerque_city": AlbuquerqueCityTransformer,
}


def get_transformer(source: SourceConfig, cfg) -> Transformer:
    try:
        cls = _REGISTRY[source.key]
    except KeyError as exc:
        raise KeyError(f"No transformer registered for source {source.key!r}") from exc
    return cls(source, cfg)


__all__ = ["Transformer", "get_transformer"]
