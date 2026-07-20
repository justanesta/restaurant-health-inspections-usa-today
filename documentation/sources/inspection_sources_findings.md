# Inspection Sources — Findings

**Status:** Active (append-only, dated) · As-built observations from probing the live sources. These
are observations that can change upstream, distinct from the ADRs in [decisions/](../decisions/) and
the stable mapping in [data-schemas.md](../data-schemas.md).

## 2026-07-18: initial probe of all three sources

### New York State: Socrata SODA API (dataset `cnih-y5dw`)
- Live, keyless JSON. **21,574 rows** total, with `$limit`/`$offset` pagination and `$where`/`$order`
  for filtering and sorting.
- Grain: **one row per establishment = its LAST inspection only.** Historical inspections live in a
  *separate* dataset (`2hcc-shji`), and inactive/closed establishments in yet another (`aaxz-j6pj`);
  either could be integrated for more coverage.
- Ships **lat/long** in `location1`, so NY could get tract-level FIPS with no address geocoding.
- Violations are pre-aggregated: a single `violations` text blob (segments like `Item 12D- …`) plus
  counts `total_critical_violations` / `total_crit_not_corrected` / `total_noncritical_violations`.
- **Excludes** NYC, Suffolk County, and Erie County (they run their own systems), so the county set is
  the rest of NY State. In the 90-day slice we saw **47 distinct counties across 400 rows**.
- `nys_health_operation_id` is the *operation/establishment* id, not a per-inspection id. We key the
  inspection as `operation_id|date`.

### Los Angeles County: ArcGIS Hub CSV ×2
- Live and keyless. The inspections CSV is about **24 MB** (3 years); violations are a second, smaller
  file. Join on `SERIAL NUMBER`.
- Grain: **one row per program-element per inspection**. A single facility (e.g. a hotel) emits many
  rows (bakery, pool bar, restaurant), each with its own `SERIAL NUMBER` and `SCORE`.
- The header also carries `EMPLOYEE ID` (inspections) and `POINTS` (violations). Both `SCORE` (0–100)
  and a letter `GRADE` are present.
- **Encoding gotcha**: the export mixes UTF-8 with stray CP1252 bytes (e.g. a `0x92` smart quote), so
  the reader falls back from UTF-8 to CP1252 to latin-1.
- Excludes Pasadena, Long Beach, and Vernon, which run their own health departments.

### City of Albuquerque: weekly "Media Report" PDF
- Live, and it appears to be overwritten weekly. Parses with `pdftotext -layout`. It's a **rolling
  latest-week snapshot** (the probed copy: Jul 5–11 2026, "Amended … for clerical errors"). The
  filename is static but the content changes weekly, so history has to be accumulated across pulls.
- Two layers: a **summary table** (pp. 1–4, clean) and **detail pages** (pp. 5–37, free-text
  violation narrative). The summary has no violations and no score.
- Statuses observed: `Approved`, `Conditional Approved`, `Unsatisfactory Re-Inspection required`,
  `Closure Re-Inspection Required`; plus operational `Open`/`Closed`.
- `Inspection ID Number` is **not always unique** (sometimes it's just the permit #), so the key is
  composite.
- No ZIP in the summary; the address is a street line, with city Albuquerque implied.
- Edge cases the parser must handle (all present in one real report and covered by tests): multiple
  permits per establishment, multiple inspections per establishment same day, en-dash vs hyphen,
  repeated address text, page footers interleaved.

### Enrichment: Census
- **Geocoder** (address → county/tract FIPS + GEOID): keyless, works.
- **ACS data API** (FIPS → population/demographics): now **requires a free key**. This is why
  enrichment is hard-coded in this PoC ([ADR 0002](../decisions/0002-hardcoded-census-enrichment.md)).
