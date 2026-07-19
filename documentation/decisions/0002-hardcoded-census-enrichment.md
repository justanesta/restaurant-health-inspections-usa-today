# 0002 — Hard-code county FIPS + population (no live Census API)

**Status:** Accepted (2026-07-18)

## Context
Each record should carry a US Census FIPS/GEOID and basic demographics (population). Two Census
services exist: the **Geocoder** (address → county FIPS, keyless) and the **ACS data API** (FIPS →
demographics). During the build we confirmed the ACS data API now **requires a free key**
(unauthenticated calls redirect to a "Missing Key" page). For a PoC we don't want a runtime
dependency on a keyed external API.

## Decision
Enrich at **county level** from a committed static file, `config/geo_reference.yaml`:
- **FIPS/GEOID** — stable public identifiers → hard-coded in full and treated as authoritative.
- **population** — a time-varying measure → hard-coded **snapshot** (approx. ACS 2019–2023 5-yr) for
  headline counties; unknown counties get `population: null` **plus an `enrichment_note`** — flagged,
  never fabricated.
The pipeline never calls Census at runtime. `scripts/build_geo_reference.py` documents (and, with a
key, performs) the refresh from live ACS.

## Consequences
- Zero runtime external dependency; deterministic, offline-testable enrichment.
- Population coverage is partial by design; the null+note pattern makes the gap visible and is the
  same mechanism a real refresh would fill.
- **Upgrade path** (documented, not wired): swap `geo_reference` for a Geocoder call (address → tract
  FIPS) + ACS call (FIPS → any demographics a beat cares about). County → tract is a config/loader
  change, not a schema change. A publication can widen the demographics per its interest.
