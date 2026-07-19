"""County-level geographic enrichment.

Attaches county FIPS/GEOID + a population snapshot from the hard-coded
config/geo_reference.yaml (ADR 0002). FIPS are stable public identifiers and are
authoritative here; population is a hard-coded snapshot and may be null (flagged).

Upgrade path (documented, not wired into the pipeline):
  * address -> county FIPS : Census Geocoder (keyless)
  * FIPS   -> demographics : Census ACS 5-year (needs a free key)
See scripts/build_geo_reference.py and documentation/decisions/0002-*.md.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import yaml

from .paths import GEO_REFERENCE


class GeoReference:
    def __init__(self, doc: dict[str, Any]):
        self.vintage: str = doc.get("population_vintage", "")
        self.counties: dict[str, dict[str, Any]] = doc["counties"]
        # Index for name-based lookup (NY gives county names, not FIPS).
        # key = (state_fips, normalized county name) -> fips
        self._name_index: dict[tuple[str, str], str] = {}
        for fips, rec in self.counties.items():
            key = (rec["state_fips"], _norm_county(rec["name"]))
            self._name_index[key] = fips

    def by_fips(self, fips: str) -> dict[str, Any]:
        rec = self.counties.get(fips)
        if rec is None:
            return _miss(county_fips=fips, enrichment_note=f"FIPS {fips} not in geo_reference.yaml")
        return self._geo(fips, rec)

    def by_county_name(self, name: str | None, state_fips: str) -> dict[str, Any]:
        if not name:
            return _miss(state_fips=state_fips, enrichment_note="empty county name")
        fips = self._name_index.get((state_fips, _norm_county(name)))
        if fips is None:
            return _miss(
                county_name=name.title(),
                state_fips=state_fips,
                enrichment_note=f"county {name!r} (state {state_fips}) not in geo_reference.yaml",
            )
        return self._geo(fips, self.counties[fips])

    def _geo(self, fips: str, rec: dict[str, Any]) -> dict[str, Any]:
        pop = rec.get("population")
        note = None if pop is not None else "population not in hard-coded snapshot; refresh via Census ACS"
        return {
            "county_name": rec["name"],
            "county_fips": fips,
            "state_fips": rec["state_fips"],
            "state": rec["state"],
            "population": pop,
            "population_vintage": self.vintage if pop is not None else None,
            "enrichment_note": note,
        }


def _norm_county(name: str) -> str:
    # Case/punctuation-insensitive: "St. Lawrence" (reference) == "ST LAWRENCE" (NY data).
    return name.upper().replace(" COUNTY", "").replace(".", "").strip()


def _miss(**kw: Any) -> dict[str, Any]:
    base = {
        "county_name": None,
        "county_fips": None,
        "state_fips": None,
        "state": None,
        "population": None,
        "population_vintage": None,
        "enrichment_note": None,
    }
    base.update(kw)
    return base


@lru_cache(maxsize=1)
def load_geo_reference(path=GEO_REFERENCE) -> GeoReference:
    with open(path) as fh:
        return GeoReference(yaml.safe_load(fh))
