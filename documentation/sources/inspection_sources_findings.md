# Inspection Sources — Findings

**Status:** Active (append-only, dated) · As-built observations from probing the live sources. These
are *observations that can change upstream* — distinct from decisions ([decisions/](../decisions/))
and the stable mapping ([data-schemas.md](../data-schemas.md)).

## 2026-07-18 — initial probe of all three sources

### New York State — Socrata SODA (`cnih-y5dw`)
- Live, keyless JSON. **21,574 rows** total; `$limit/$offset` pagination; `$where`/`$order` work.
- Grain: **one row per establishment = its LAST inspection only.** Historical inspections are a
  *separate* dataset (`2hcc-shji`); inactive/closed establishments another (`aaxz-j6pj`).
- Ships **lat/long** in `location1` — so NY could get tract-level FIPS with no address geocoding.
- Violations are pre-aggregated: a single `violations` text blob (segments like `Item 12D- …`) plus
  counts `total_critical_violations` / `total_crit_not_corrected` / `total_noncritical_violations`.
- **Excludes** NYC, Suffolk County, and Erie County (they run their own systems) — so the county set
  is the rest of NY State. In the 90-day slice we saw **47 distinct counties / 400 rows**.
- `nys_health_operation_id` is the *operation/establishment* id, not a per-inspection id → inspection
  key is `operation_id|date`.

### Los Angeles County — ArcGIS Hub CSV ×2
- Live, keyless. Inspections CSV ≈ **24 MB** (3 years); violations a second file. Join on
  `SERIAL NUMBER`.
- Grain: **one row per program-element per inspection** — a single facility (e.g. a hotel) emits many
  rows (bakery, pool bar, restaurant), each its own `SERIAL NUMBER` + `SCORE`.
- Header carries two fields the notes didn't list: `EMPLOYEE ID` (inspections) and `POINTS`
  (violations). Has both `SCORE` (0–100) and letter `GRADE`.
- **Encoding gotcha**: the export mixes UTF-8 with stray CP1252 bytes (e.g. `0x92` smart quote) → the
  reader falls back UTF-8 → CP1252 → latin-1.
- Excludes Pasadena, Long Beach, Vernon (own health departments).

### City of Albuquerque — weekly "Media Report" PDF
- Live, keyless, 37 pp., parses with `pdftotext -layout`. **Rolling latest-week snapshot** (probed
  copy: Jul 5–11 2026, "Amended … for clerical errors") — the filename is static, content changes
  weekly, so history must be accumulated across pulls.
- Two layers: **summary table** (pp. 1–4, clean) vs **detail pages** (pp. 5–37, free-text violation
  narrative). Summary has no violations and no score.
- Statuses observed: `Approved`, `Conditional Approved`, `Unsatisfactory Re-Inspection required`,
  `Closure Re-Inspection Required`; plus operational `Open`/`Closed`. (Confirms the draft "only Closed
  = fail" rule was wrong — see [ADR 0001](../decisions/0001-thin-pass-fail-result.md).)
- `Inspection ID Number` is **not always unique** (sometimes it's just the permit #) → composite key.
- No ZIP in the summary; address is a street line, city = Albuquerque implied.
- Edge cases the parser must handle (all present in one real report and covered by tests): multiple
  permits per establishment, multiple inspections per establishment same day, en-dash vs hyphen,
  repeated address text, page footers interleaved.

### Enrichment — Census
- **Geocoder** (address → county/tract FIPS + GEOID): keyless, works.
- **ACS data API** (FIPS → population/demographics): now **requires a free key** (unauthenticated
  requests redirect to a "Missing Key" page). This is why enrichment is hard-coded
  ([ADR 0002](../decisions/0002-hardcoded-census-enrichment.md)).
