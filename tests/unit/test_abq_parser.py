"""Albuquerque PDF summary-table parser — the highest-risk extractor."""

from __future__ import annotations

from inspections.extractors.albuquerque import _dedupe_address, parse_summary


def test_parses_expected_rows(abq_text):
    rows = parse_summary(abq_text)
    assert len(rows) >= 10
    assert all(r["establishment_name"] and r["inspection_date"] for r in rows)


def test_multi_permit_establishment(abq_text):
    # EFFING BAR AND GRILL appears with two distinct permits, each its own row.
    effing = [r for r in parse_summary(abq_text) if "EFFING" in r["establishment_name"].upper()]
    permits = {r["permit"] for r in effing}
    assert len(effing) == 2
    assert len(permits) == 2


def test_multi_inspection_same_establishment(abq_text):
    amaran = [r for r in parse_summary(abq_text) if "AMARAN" in r["establishment_name"].upper()]
    assert len(amaran) == 2  # a Corrective Action + a Routine, same day


def test_closed_and_unsatisfactory_captured(abq_text):
    rows = parse_summary(abq_text)
    eat = next(r for r in rows if "EAT MY THAI" in r["establishment_name"].upper())
    assert eat["operational_status"].lower() == "closed"
    bamboo = next(r for r in rows if "BAMBOO" in r["establishment_name"].upper())
    assert "unsatisfactory" in bamboo["inspection_status"].lower()


def test_dedupe_repeated_address():
    assert _dedupe_address("5604 MENAUL BLVD NE 5604 MENAUL BLVD NE") == "5604 MENAUL BLVD NE"
    assert _dedupe_address("809 98TH ST SW") == "809 98TH ST SW"
