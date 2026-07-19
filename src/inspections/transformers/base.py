"""Transformer base: read a source's raw data, emit unified-schema record dicts.

A transformer is a pure mapping from source-native raw records to the unified shape.
It does NOT validate — the pipeline's transform stage runs the pydantic contract over
the emitted dicts and routes failures to an ErrorSink (post-transform validation).
`assemble()` builds the common envelope (ids, provenance, geography, timestamps) so each
source transformer only supplies the fields that actually differ.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .. import SCHEMA_VERSION, paths
from ..config import PipelineConfig, SourceConfig
from ..ids import establishment_uuid, inspection_uuid
from ..state import read_state


class Transformer(ABC):
    def __init__(self, source: SourceConfig, cfg: PipelineConfig):
        self.source = source
        self.cfg = cfg

    @property
    def raw_dir(self) -> Path:
        return paths.RAW_DIR / self.source.key

    def _extracted_at(self) -> str | None:
        stages = read_state(self.source.key).get("stages", {})
        return stages.get("extract", {}).get("at")

    def source_metadata(self) -> dict[str, Any]:
        return {
            "source_name": self.source.name,
            "publisher": self.source.publisher,
            "landing_url": self.source.landing_url,
            "extraction_method": self.source.extraction_method.value,
            "source_dataset_id": self.source.dataset_id,
            "extracted_at": self._extracted_at(),
        }

    def assemble(
        self,
        *,
        source_inspection_id: str,
        source_establishment_id: str | None,
        restaurant_name: str,
        address: dict[str, Any],
        inspection_date: str,
        inspection_type: str | None,
        result: str,
        result_basis: str,
        geography: dict[str, Any],
        score: float | None = None,
        grade: str | None = None,
        critical_violation_count: int | None = None,
        total_violation_count: int | None = None,
        violations: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        estab_key = source_establishment_id or source_inspection_id
        return {
            "schema_version": SCHEMA_VERSION,
            "inspection_uuid": inspection_uuid(self.source.key, source_inspection_id),
            "establishment_uuid": establishment_uuid(self.source.key, estab_key),
            "source": self.source.key,
            "source_inspection_id": source_inspection_id,
            "source_establishment_id": source_establishment_id,
            "restaurant_name": restaurant_name,
            "address": address,
            "inspection_date": inspection_date,
            "inspection_type": inspection_type,
            "inspection_result": result,
            "result_basis": result_basis,
            "score": score,
            "grade": grade,
            "critical_violation_count": critical_violation_count,
            "total_violation_count": total_violation_count,
            "violations": violations or [],
            "geography": geography,
            "source_metadata": self.source_metadata(),
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        }

    @abstractmethod
    def transform(self) -> list[dict[str, Any]]: ...


# --- small shared normalizers -------------------------------------------------

def us_date_to_iso(value: str) -> str:
    """'07/08/2026' -> '2026-07-08'."""
    return datetime.strptime(value.strip(), "%m/%d/%Y").date().isoformat()


def iso_prefix(value: str) -> str:
    """'2026-06-16T00:00:00.000' -> '2026-06-16'."""
    return value.strip()[:10]
