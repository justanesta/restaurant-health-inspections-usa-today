"""County enrichment: FIPS resolution, population snapshot, and graceful misses."""

from __future__ import annotations

from inspections.enrichment import GeoReference, load_geo_reference
from inspections.models import Geography


def geo():
    return load_geo_reference()


def test_by_fips_known_county_has_population():
    g = geo().by_fips("06037")
    assert g["county_name"] == "Los Angeles"
    assert g["population"] and g["population"] > 0
    assert g["enrichment_note"] is None


def test_by_county_name_resolves_fips():
    g = geo().by_county_name("MONROE", "36")
    assert g["county_fips"] == "36055"


def test_stlawrence_punctuation_insensitive():
    # geo_reference has "St. Lawrence"; NY data says "ST LAWRENCE"
    g = geo().by_county_name("ST LAWRENCE", "36")
    assert g["county_fips"] == "36089"


def test_known_county_now_has_population():
    g = geo().by_county_name("TOMPKINS", "36")
    assert g["county_fips"] == "36109"
    assert g["population"] and g["population"] > 0


def test_null_population_is_flagged_not_fabricated():
    # A county present in the reference but WITHOUT a population must be flagged, not guessed.
    ref = GeoReference({
        "population_vintage": "test",
        "counties": {"99123": {"name": "Nowhere", "state": "ZZ", "state_fips": "99", "population": None}},
    })
    g = ref.by_fips("99123")
    assert g["county_fips"] == "99123"
    assert g["population"] is None
    assert "refresh" in (g["enrichment_note"] or "")
    Geography.model_validate(g)


def test_unknown_county_returns_valid_geography_with_note():
    g = geo().by_county_name("ATLANTIS", "36")
    assert g["county_fips"] is None
    assert g["enrichment_note"]
    Geography.model_validate(g)  # must still satisfy the (extra=forbid) contract
