"""Loud error sink + per-source state file."""

from __future__ import annotations

from inspections.errors import ErrorSink
from inspections.state import read_state, record_stage


def test_empty_sink_writes_nothing(hermetic_data):
    sink = ErrorSink("transform", "new_york_state")
    assert sink.flush() is None
    assert not sink


def test_sink_writes_findable_report(hermetic_data, capsys):
    sink = ErrorSink("transform", "new_york_state")
    sink.record("row#3", "post-transform validation failed", "inspection_date: invalid")
    path = sink.flush()
    assert path is not None and path.exists()
    body = path.read_text()
    assert "DATA QUALITY ERRORS" in body
    assert "row#3" in body
    # loud: a banner is printed to stderr
    assert "DATA QUALITY ERROR" in capsys.readouterr().err


def test_state_roundtrip(hermetic_data):
    record_stage("new_york_state", "extract", "success", {"records": 400})
    st = read_state("new_york_state")
    assert st["stages"]["extract"]["status"] == "success"
    assert st["stages"]["extract"]["records"] == 400
    assert st["updated_at"]
