"""Loader: merge validated staging records into the combined production dataset."""

from __future__ import annotations

from .combine import LoadResult, combine

__all__ = ["LoadResult", "combine"]
