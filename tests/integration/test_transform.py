"""Per-source transform: fixture raw -> normalized records that satisfy the contract."""

from __future__ import annotations

import json

import pytest

from inspections.config import load_config
from inspections.extractors.albuquerque import parse_summary
from inspections.transformers import get_transformer
from inspections.validation import json_schema_errors, validate_records


@pytest.fixture
def cfg():
    return load_config()


def _staging(records):
    valid, errors = validate_records(records)
    assert errors == [], errors
    dumped = [m.model_dump(mode="json") for m in valid]
    assert json_schema_errors(dumped) == []
    return {r["source_inspection_id"]: r for r in dumped}


def test_new_york_transform(hermetic_data, cfg, ny_records):
    raw = hermetic_data / "raw" / "new_york_state"
    raw.mkdir(parents=True)
    (raw / "inspections.json").write_text(json.dumps(ny_records))

    recs = get_transformer(cfg.get("new_york_state"), cfg).transform()
    by_id = _staging(recs)

    risky = by_id["222|2026-05-15"]
    assert risky["inspection_result"] == "fail"          # 2 critical not corrected
    assert risky["critical_violation_count"] == 3
    good = by_id["111|2026-06-01"]
    assert good["inspection_result"] == "pass"
    assert len(good["violations"]) == 2                   # blob split on Item markers
    nowhere = by_id["333|2026-04-30"]
    assert nowhere["geography"]["county_fips"] is None    # ATLANTIS -> flagged miss
    assert nowhere["geography"]["enrichment_note"]


def test_los_angeles_transform(hermetic_data, cfg, la_inspections_csv, la_violations_csv):
    raw = hermetic_data / "raw" / "los_angeles_county"
    raw.mkdir(parents=True)
    (raw / "inspections.csv").write_bytes(la_inspections_csv)
    (raw / "violations.csv").write_bytes(la_violations_csv)

    recs = get_transformer(cfg.get("los_angeles_county"), cfg).transform()
    by_id = _staging(recs)

    assert by_id["DA111"]["inspection_result"] == "pass"     # score 95
    bad = by_id["DA222"]
    assert bad["inspection_result"] == "fail"                # score 65
    assert bad["critical_violation_count"] == 1              # the 4-point violation
    assert bad["total_violation_count"] == 2
    assert by_id["DA333"]["violations"] == []                # score 100, no violations
    assert by_id["DA111"]["geography"]["county_fips"] == "06037"


def test_albuquerque_transform(hermetic_data, cfg, abq_text):
    raw = hermetic_data / "raw" / "albuquerque_city"
    raw.mkdir(parents=True)
    (raw / "summary.json").write_text(json.dumps(parse_summary(abq_text)))

    recs = get_transformer(cfg.get("albuquerque_city"), cfg).transform()
    _staging(recs)

    by_name = {r["restaurant_name"].upper(): r for r in recs}
    assert "closed" in by_name["EAT MY THAI CUISINE"]["result_basis"].lower() or \
        by_name["EAT MY THAI CUISINE"]["inspection_result"] == "fail"
    assert by_name["EAT MY THAI CUISINE"]["inspection_result"] == "fail"
    assert by_name["BAMBOO"]["inspection_result"] == "fail"
    assert all(r["violations"] == [] for r in recs)          # summary-only
    assert all(r["geography"]["county_fips"] == "35001" for r in recs)
