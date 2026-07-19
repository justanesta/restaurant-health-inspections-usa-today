"""Filesystem layout for the pipeline.

Repo root is found by walking up from this file until pyproject.toml is seen, so
the package works whether invoked from the repo root, a subdir, or CI.

The DATA root is redirectable: set INSPECTIONS_DATA_DIR, or call use_data_dir() (tests
point it at a tmp dir). Consumers reference `paths.RAW_DIR` etc. at call-time so the
redirect takes effect everywhere.
"""

from __future__ import annotations

import os
from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / "pyproject.toml").is_file():
            return parent
    # Fallback: src/inspections/paths.py -> repo root is two levels up from src.
    return start.parents[2]


REPO_ROOT = _find_repo_root(Path(__file__).resolve())

CONFIG_DIR = REPO_ROOT / "config"
SCHEMA_DIR = REPO_ROOT / "schema"

SOURCES_CONFIG = CONFIG_DIR / "sources.yaml"
GEO_REFERENCE = CONFIG_DIR / "geo_reference.yaml"
SCHEMA_YAML = SCHEMA_DIR / "inspection_schema.yaml"
SCHEMA_JSON = SCHEMA_DIR / "inspection.schema.json"

def use_data_dir(root: str | Path) -> None:
    """Point the data-stage folders at `root`. Consumers read these at call-time."""
    global DATA_DIR, RAW_DIR, STAGING_DIR, PRODUCTION_DIR, ERRORS_DIR, STATE_DIR
    DATA_DIR = Path(root)
    RAW_DIR = DATA_DIR / "raw"
    STAGING_DIR = DATA_DIR / "staging"
    PRODUCTION_DIR = DATA_DIR / "production"
    ERRORS_DIR = DATA_DIR / "errors"
    STATE_DIR = DATA_DIR / "state"


# Initialize from env (or default to <repo>/data).
use_data_dir(os.environ.get("INSPECTIONS_DATA_DIR") or (REPO_ROOT / "data"))


def ensure_data_dirs() -> None:
    """Create the data-stage folders if missing (safe to call repeatedly)."""
    for d in (RAW_DIR, STAGING_DIR, PRODUCTION_DIR, ERRORS_DIR, STATE_DIR):
        d.mkdir(parents=True, exist_ok=True)
