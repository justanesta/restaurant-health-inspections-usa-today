"""Per-source pipeline state.

One small JSON file per source under data/state/ records the outcome of each stage
(extract / transform / load): status, timestamp, and metrics (row counts, the window
used, a source fingerprint, error count). It answers "what happened on the last run and
is the pipeline healthy?" at a glance, and gives later stages something to check.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import paths


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def state_path(source: str) -> Path:
    return paths.STATE_DIR / f"{source}.json"


def read_state(source: str) -> dict[str, Any]:
    p = state_path(source)
    if p.exists():
        return json.loads(p.read_text())
    return {"source": source, "stages": {}, "updated_at": None}


def record_stage(
    source: str,
    stage: str,
    status: str,
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist the outcome of one stage. status in {'success','failed','partial'}."""
    st = read_state(source)
    st["source"] = source
    st.setdefault("stages", {})[stage] = {
        "status": status,
        "at": _now(),
        **(metrics or {}),
    }
    st["updated_at"] = _now()
    paths.ensure_data_dirs()
    state_path(source).write_text(json.dumps(st, indent=2) + "\n")
    return st
