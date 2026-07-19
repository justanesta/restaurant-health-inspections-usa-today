"""Extractors run against fixture payloads (network + pdftotext mocked)."""

from __future__ import annotations

import json

import pytest

from inspections.config import load_config
from inspections.extractors import get_extractor


@pytest.fixture
def cfg():
    return load_config()


def test_new_york_extractor(hermetic_data, cfg, ny_records, monkeypatch):
    calls = {"n": 0}

    def fake_fetch_json(url, **kw):
        # first page returns the fixture, subsequent pages are empty
        calls["n"] += 1
        return ny_records if "offset=0" in url else []

    monkeypatch.setattr("inspections.extractors.new_york.fetch_json", fake_fetch_json)
    result = get_extractor(cfg.get("new_york_state"), cfg).extract()

    assert result.record_count == len(ny_records)
    assert result.missing_expected == []
    saved = json.loads((hermetic_data / "raw" / "new_york_state" / "inspections.json").read_text())
    assert len(saved) == len(ny_records)


def test_los_angeles_extractor(hermetic_data, cfg, la_inspections_csv, la_violations_csv, monkeypatch):
    def fake_fetch_bytes(url, **kw):
        return la_violations_csv if "5eaea9" in url else la_inspections_csv

    monkeypatch.setattr("inspections.extractors.los_angeles.fetch_bytes", fake_fetch_bytes)
    result = get_extractor(cfg.get("los_angeles_county"), cfg).extract()

    assert result.record_count == 3
    assert result.missing_expected == []
    assert result.notes["violation_rows"] == 3


def test_albuquerque_extractor(hermetic_data, cfg, abq_text, monkeypatch):
    monkeypatch.setattr("inspections.extractors.albuquerque.fetch_bytes", lambda url, **kw: b"%PDF-1.6 dummy")
    monkeypatch.setattr("inspections.extractors.albuquerque.pdf_to_text", lambda p: abq_text)
    result = get_extractor(cfg.get("albuquerque_city"), cfg).extract()

    assert result.record_count >= 10
    assert result.missing_expected == []
    assert result.notes["report_week"]


def test_extractor_flags_upstream_drift(hermetic_data, cfg, ny_records, monkeypatch):
    """A missing expected field must be reported (not silently ignored)."""
    dropped = [{k: v for k, v in r.items() if k != "county"} for r in ny_records]
    monkeypatch.setattr(
        "inspections.extractors.new_york.fetch_json",
        lambda url, **kw: dropped if "offset=0" in url else [],
    )
    result = get_extractor(cfg.get("new_york_state"), cfg).extract()
    assert "county" in result.missing_expected
    assert not result.ok
