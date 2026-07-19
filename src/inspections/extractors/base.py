"""Extractor base: fetch a source's native data into data/raw/, detect upstream drift.

Each extractor lands SOURCE-NATIVE data (JSON / CSV / PDF+text) under
data/raw/<source>/ and returns an ExtractResult. It also checks that the fields it
depends on are still present (EXPECTED_FIELDS) — the first line of defence against a
source silently changing shape.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .. import paths
from ..config import PipelineConfig, SourceConfig


@dataclass
class ExtractResult:
    source: str
    extracted_at: str
    raw_paths: list[Path]
    record_count: int
    fields_present: list[str]
    missing_expected: list[str]
    fingerprint: str
    notes: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.missing_expected


class Extractor(ABC):
    #: Fields the downstream transform relies on. Missing => upstream drift.
    EXPECTED_FIELDS: tuple[str, ...] = ()

    def __init__(self, source: SourceConfig, cfg: PipelineConfig):
        self.source = source
        self.cfg = cfg

    @property
    def raw_dir(self) -> Path:
        d = paths.RAW_DIR / self.source.key
        d.mkdir(parents=True, exist_ok=True)
        return d

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def fingerprint(field_names: list[str]) -> str:
        """Stable hash of the sorted field set — changes iff the source schema changes."""
        blob = "|".join(sorted(field_names)).encode()
        return hashlib.sha256(blob).hexdigest()[:16]

    def check_fields(self, present: list[str]) -> list[str]:
        have = set(present)
        return [f for f in self.EXPECTED_FIELDS if f not in have]

    @abstractmethod
    def extract(self) -> ExtractResult: ...
