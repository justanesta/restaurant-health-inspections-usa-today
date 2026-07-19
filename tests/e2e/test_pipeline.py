"""End-to-end pipeline: mocked sources through to a validated production file,
plus a drift scenario, plus an opt-in live-network run."""

from __future__ import annotations

import json

import jsonschema
import pytest

from inspections import paths
from inspections.pipeline import main


@pytest.fixture
def mock_sources(monkeypatch, ny_records, la_inspections_csv, la_violations_csv, abq_text):
    monkeypatch.setattr(
        "inspections.extractors.new_york.fetch_json",
        lambda url, **kw: ny_records if "offset=0" in url else [],
    )
    monkeypatch.setattr(
        "inspections.extractors.los_angeles.fetch_bytes",
        lambda url, **kw: la_violations_csv if "5eaea9" in url else la_inspections_csv,
    )
    monkeypatch.setattr("inspections.extractors.albuquerque.fetch_bytes", lambda url, **kw: b"%PDF dummy")
    monkeypatch.setattr("inspections.extractors.albuquerque.pdf_to_text", lambda p: abq_text)


def _production():
    return json.loads((paths.PRODUCTION_DIR / "inspections.json").read_text())


def test_full_run_produces_validated_production(hermetic_data, mock_sources):
    assert main(["run"]) == 0

    records = _production()
    assert len(records) == 19  # 3 NY + 3 LA + 13 ABQ

    schema = json.loads(paths.SCHEMA_JSON.read_text())
    validator = jsonschema.Draft202012Validator(schema)
    for r in records:
        assert not list(validator.iter_errors(r))

    manifest = json.loads((paths.PRODUCTION_DIR / "manifest.json").read_text())
    assert manifest["total_inspections"] == 19
    assert manifest["per_source"] == {"new_york_state": 3, "los_angeles_county": 3, "albuquerque_city": 13}

    # every enabled source recorded a successful load state
    for key in ("new_york_state", "los_angeles_county", "albuquerque_city"):
        st = json.loads((paths.STATE_DIR / f"{key}.json").read_text())
        assert st["stages"]["load"]["status"] == "success"


def test_upstream_drift_fails_loudly_and_skips_transform(hermetic_data, monkeypatch, ny_records,
                                                         la_inspections_csv, la_violations_csv, abq_text):
    # NY loses a column -> drift; LA + ABQ are healthy.
    dropped = [{k: v for k, v in r.items() if k != "county"} for r in ny_records]
    monkeypatch.setattr(
        "inspections.extractors.new_york.fetch_json",
        lambda url, **kw: dropped if "offset=0" in url else [],
    )
    monkeypatch.setattr(
        "inspections.extractors.los_angeles.fetch_bytes",
        lambda url, **kw: la_violations_csv if "5eaea9" in url else la_inspections_csv,
    )
    monkeypatch.setattr("inspections.extractors.albuquerque.fetch_bytes", lambda url, **kw: b"%PDF dummy")
    monkeypatch.setattr("inspections.extractors.albuquerque.pdf_to_text", lambda p: abq_text)

    assert main(["run"]) == 1  # non-zero: errors occurred

    # a findable error report exists for NY extract
    reports = list((paths.ERRORS_DIR).glob("extract__new_york_state__*.txt"))
    assert reports, "expected a quarantine report for NY drift"

    # NY was skipped downstream; LA + ABQ still made it to production
    ny_state = json.loads((paths.STATE_DIR / "new_york_state.json").read_text())
    assert ny_state["stages"]["extract"]["status"] == "failed"
    assert not (paths.STAGING_DIR / "new_york_state.json").exists()
    sources = {r["source"] for r in _production()}
    assert sources == {"los_angeles_county", "albuquerque_city"}


@pytest.mark.network
def test_live_sources_smoke(hermetic_data):
    """Opt-in: hit the real endpoints. Run with `pytest -m network`."""
    assert main(["run"]) == 0
    records = _production()
    assert len(records) > 100
    assert {r["source"] for r in records} == {
        "new_york_state", "los_angeles_county", "albuquerque_city",
    }
