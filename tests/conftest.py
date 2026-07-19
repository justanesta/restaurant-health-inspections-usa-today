"""Shared test fixtures.

`hermetic_data` redirects the pipeline's data root at a tmp dir so tests never touch the
committed data/ slice. `fixtures` points at tests/fixtures/.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from inspections import paths
from inspections.config import load_config

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures() -> Path:
    return FIXTURES


@pytest.fixture
def hermetic_data(tmp_path, monkeypatch):
    """Point all data-stage folders at a tmp dir for the duration of a test."""
    old = paths.DATA_DIR
    paths.use_data_dir(tmp_path / "data")
    paths.ensure_data_dirs()
    yield paths.DATA_DIR
    paths.use_data_dir(old)


@pytest.fixture
def cfg():
    return load_config()


@pytest.fixture
def ny_records() -> list[dict]:
    return json.loads((FIXTURES / "ny_sample.json").read_text())


@pytest.fixture
def la_inspections_csv() -> bytes:
    return (FIXTURES / "la_inspections.csv").read_bytes()


@pytest.fixture
def la_violations_csv() -> bytes:
    return (FIXTURES / "la_violations.csv").read_bytes()


@pytest.fixture
def abq_text() -> str:
    return (FIXTURES / "abq_summary.txt").read_text()
