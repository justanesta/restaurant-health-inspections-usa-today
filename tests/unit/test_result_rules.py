"""The fixed pass/fail derivation rules (ADR 0001), one per source."""

from __future__ import annotations

import pytest

from inspections.transformers.albuquerque import derive_result
from inspections.transformers.new_york import split_violations


@pytest.mark.parametrize("status,op,expected", [
    ("Approved", "Open", "pass"),
    ("Conditional Approved", "Open", "pass"),
    ("Unsatisfactory Re-Inspection required", "Open", "fail"),
    ("Closure Re-Inspection Required", "Closed", "fail"),
    ("Approved", "Closed", "fail"),  # operational status Closed overrides
])
def test_abq_result(status, op, expected):
    result, basis = derive_result(status, op)
    assert result == expected
    assert status in basis


def test_ny_violation_split():
    assert split_violations("") == []
    assert split_violations(None) == []
    multi = split_violations("Item  8A-  first thing; Item  9B-  second thing")
    assert len(multi) == 2
    # text without an Item marker stays a single violation
    assert len(split_violations("General note, no item marker")) == 1
