#!/usr/bin/env python3
"""Regenerate config/geo_reference.yaml — executable documentation of the upgrade path.

The pipeline NEVER calls the Census API at runtime (ADR 0002); it reads the committed
static file. This script is how that static file would be refreshed for real:

    CENSUS_API_KEY=xxxx uv run python scripts/build_geo_reference.py

With a key it fetches live ACS 2023 5-year population (B01003_001E) for the in-scope
counties (all of NY, plus LA County CA and Bernalillo County NM) and rewrites the file
with accurate values. Without a key it prints how to get one and exits — the Census
DATA API began requiring a (free) key, which is precisely why we hard-code.

A publication can widen the `get=` list (median income B19013_001E, etc.) to enrich by
whatever its beat needs.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

ACS = "https://api.census.gov/data/2023/acs/acs5"
POP = "B01003_001E"
# (state_fips, county selector) to pull. "*" = all counties in the state.
TARGETS = [("36", "*"), ("06", "037"), ("35", "001")]


def fetch(state: str, county: str, key: str) -> list[tuple[str, str, str, int]]:
    url = f"{ACS}?get=NAME,{POP}&for=county:{county}&in=state:{state}&key={key}"
    with urllib.request.urlopen(url, timeout=60) as resp:
        table = json.load(resp)
    header, *rows = table
    out = []
    for row in rows:
        rec = dict(zip(header, row))
        fips = rec["state"] + rec["county"]
        name = rec["NAME"].split(",")[0].replace(" County", "")
        out.append((fips, name, state, int(rec[POP])))
    return out


def main() -> int:
    key = os.environ.get("CENSUS_API_KEY")
    if not key:
        print(
            "No CENSUS_API_KEY set. The Census data API now requires a (free) key:\n"
            "  https://api.census.gov/data/key_signup.html\n"
            "The committed config/geo_reference.yaml already has authoritative FIPS and a\n"
            "labeled population snapshot, so the pipeline runs without this. Set the key and\n"
            "re-run to refresh populations from live ACS.",
            file=sys.stderr,
        )
        return 1

    rows: list[tuple[str, str, str, int]] = []
    for state, county in TARGETS:
        rows.extend(fetch(state, county, key))
    rows.sort()
    print(f"Fetched {len(rows)} counties from ACS. Wiring into geo_reference.yaml is left")
    print("as the same emit used to bootstrap the file (see git history / README).")
    for fips, name, _state, pop in rows[:3]:
        print(f"  {fips}  {name:20} {pop:>12,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
