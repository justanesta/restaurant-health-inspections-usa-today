"""Combine per-source staging JSON into the final production dataset.

This is the LOAD stage. It runs a final JSON Schema validation over the merged records
(pre-load gate: block downstream pollution). If any record fails, the load is REFUSED —
the previous production file is left untouched and the failures are quarantined to
data/errors/ — so a bad batch can never silently overwrite good production data.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .. import paths
from ..config import PipelineConfig
from ..errors import ErrorSink
from ..state import read_state
from ..validation import json_schema_errors


@dataclass
class LoadResult:
    total: int
    per_source: dict[str, int]
    result_breakdown: dict[str, int]
    schema_errors: int
    written: bool
    error_report: Any = None
    notes: dict = field(default_factory=dict)


def _staging_path(source_key: str):
    return paths.STAGING_DIR / f"{source_key}.json"


def combine(cfg: PipelineConfig) -> LoadResult:
    paths.ensure_data_dirs()
    records: list[dict[str, Any]] = []
    per_source: dict[str, int] = {}

    for src in cfg.enabled_sources():
        path = _staging_path(src.key)
        if not path.exists():
            per_source[src.key] = 0
            continue
        recs = json.loads(path.read_text())
        per_source[src.key] = len(recs)
        records.extend(recs)

    # Pre-load gate.
    errs = json_schema_errors(records)
    sink = ErrorSink("load", "combined")
    for idx, msg in errs:
        rid = records[idx].get("inspection_uuid", f"#{idx}") if idx < len(records) else f"#{idx}"
        sink.record(rid, "pre-load JSON Schema violation", msg)
    report = sink.flush()

    breakdown: dict[str, int] = {}
    for r in records:
        breakdown[r["inspection_result"]] = breakdown.get(r["inspection_result"], 0) + 1

    written = False
    if not errs:
        production_file = paths.PRODUCTION_DIR / "inspections.json"
        manifest_file = paths.PRODUCTION_DIR / "manifest.json"
        production_file.write_text(json.dumps(records, indent=2) + "\n")
        manifest_file.write_text(json.dumps(_manifest(cfg, records, per_source, breakdown), indent=2) + "\n")
        written = True

    return LoadResult(
        total=len(records),
        per_source=per_source,
        result_breakdown=breakdown,
        schema_errors=len(errs),
        written=written,
        error_report=str(report) if report else None,
    )


def _manifest(cfg, records, per_source, breakdown) -> dict[str, Any]:
    schema_versions = sorted({r.get("schema_version") for r in records})
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": schema_versions[0] if len(schema_versions) == 1 else schema_versions,
        "window_days": cfg.window_days,
        "sample_limit": cfg.sample_limit,
        "total_inspections": len(records),
        "per_source": per_source,
        "result_breakdown": breakdown,
        "sources": [
            {
                "key": s.key,
                "name": s.name,
                "extraction_method": s.extraction_method.value,
                "landing_url": s.landing_url,
                "extract_state": read_state(s.key).get("stages", {}).get("extract", {}),
            }
            for s in cfg.enabled_sources()
        ],
    }
