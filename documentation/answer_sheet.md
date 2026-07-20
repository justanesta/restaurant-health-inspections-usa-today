# Answer Sheet — Multi-Source Inspection Unifier

Addresses the five deliverables in [assignment_instructions.md](../project_scope/assignment_instructions.md).
Working proof-of-concept: `uv run inspections run` produces
[`data/production/inspections.json`](../data/production/inspections.json) from three live sources.
The reasoning behind each call lives in [decisions/](decisions/); the build is described in
[architecture.md](architecture.md).

---

## 1. The three sources & why they're structurally different

I chose them so no two share an extraction shape, to show that one automation can absorb all of them.

| Source | Structure | Extraction challenge | Grain |
|---|---|---|---|
| **New York State** | Socrata SODA **REST API** | the "easy" one: paginate, filter server-side; but data is a *last-inspection snapshot* with violations pre-aggregated into a text blob | 1 row / establishment |
| **Los Angeles County** | two **CSV flat files** on ArcGIS Hub | 24 MB download, **multi-file join** (inspections ⋈ violations on `SERIAL NUMBER`), CP1252 encoding difficulties and a program-element grain | 1 row / program / inspection |
| **City of Albuquerque** | weekly **PDF** "Media Report" | **scrape a rolling PDF**: layout parsing, no stable per-row id, no ZIP, summary-vs-detail layers, weekly snapshot (history must be accumulated) | 1 row / inspection / week |

The result covers one clean API, one bulk-file download-and-join, and one PDF scrape. I picked three
problems that are genuinely different from one another. More detail in
[sources/inspection_sources_findings.md](sources/inspection_sources_findings.md).

## 2. Normalizing different structures into one schema

**The pattern is N thin adapters over one shared spine.** Each source has an *extractor* that owns
its transport and a *transformer* that maps native fields onto the unified record. Everything else
(validation, enrichment, id-minting, load, delivery) is written once and is source-agnostic.

The unified record is **one inspection event** with violations nested
([ADR 0006](decisions/0006-record-grain.md)). It's defined once in
[`schema/inspection_schema.yaml`](../schema/inspection_schema.yaml) and enforced by a generated JSON
Schema and a pydantic model. The main normalization calls:

- **Outcome**: a thin `pass`/`fail`/`unknown` from a fixed rule per source, always paired with a
  plain-language `result_basis` ([ADR 0001](decisions/0001-thin-pass-fail-result.md)). NY keys on
  uncorrected critical violations, LA on a score below 70, ABQ on the status string. The native
  `score`, `grade`, and counts are carried through, so the flattening loses nothing. This is the
  edge-flattening the brief anticipated. A fuller build with many more sources would lift these
  per-source rules into a shared, versioned set of `result_rules` and add a normalized cross-source
  risk index (see [ADR 0001](decisions/0001-thin-pass-fail-result.md)).
- **Identity**: deterministic UUIDv5 for both inspection and establishment
  ([ADR 0007](decisions/0007-deterministic-uuids.md)), so re-runs are idempotent and loads are
  upserts. Establishment identity is scoped to each source's native facility/permit id; there's no
  fuzzy entity resolution yet ([ADR 0005](decisions/0005-establishment-identity.md)).
- **Place**: a structured `address` ([ADR 0008](decisions/0008-structured-address.md)) plus county
  FIPS/GEOID and population, hard-coded for the PoC with a documented Census upgrade path
  ([ADR 0002](decisions/0002-hardcoded-census-enrichment.md)).

Full field-by-field mapping: [data-schemas.md](data-schemas.md).

## 3. Scaling the pattern to many more sources

Adding a source means one config row, one extractor, one transformer, and a fixture. No schema,
pipeline, or loader change
([architecture.md → Adding a source](architecture.md#adding-a-source-the-scaling-story)).

The move at scale is to group adapters by platform *shape* rather than by jurisdiction. Thousands of
US health departments run a handful of platforms: Socrata, ArcGIS/Esri, HealthSpace, Accela, generic
CSV/Excel, and PDF. Write one adapter per platform, parameterized by config, and most new sources
become a config entry rather than new code. The registry (`config/sources.yaml`) is what turns
coverage into a data problem instead of a coding one. Storage and orchestration graduate from git
plus Actions to object storage, a warehouse (with dbt), and a real orchestrator
(Prefect/Dagster/Airflow) as N grows; the stage boundaries already line up with that shape.

## 4. Handling breakage (source changes or goes down)

Three independent, loud, fail-safe guards, none of which can silently corrupt production
([architecture.md → Breakage handling](architecture.md#breakage-handling)):

1. **Source changed shape**: the post-extract `EXPECTED_FIELDS` drift check flags it (a per-source
   `fingerprint` in state records the change), the source is marked failed, and its transform is
   skipped.
2. **Bad records**: the post-transform pydantic contract quarantines them to `data/errors/`
   (dead-letter) while good records proceed.
3. **Polluted batch**: the pre-load JSON Schema gate refuses the load and leaves prior production
   intact.

**Source down**: `http.py` separates transient failures (5xx, timeouts; retried with backoff) from
permanent ones (4xx; fail fast). A stage's non-zero exit stops the downstream stages (they trigger on
success only), so the last good production file persists until the source recovers. Every failure
leaves a findable plain-text report in `data/errors/` and a status in `data/state/`. An automated
drift test covers this (`tests/e2e/test_pipeline.py`). In production this becomes Great Expectations
or Soda at the gate, Sentry on transport errors, and per-source freshness SLAs.

## 5. Delivery: surfacing newsworthy signals to reporters

The committed `data/production/inspections.json` is already a delivery endpoint. Its raw GitHub URL
drops straight into a Slack webhook, an email blast, or (reshaped) an RSS feed, with no server
needed. On top of that one file:

- **Alerts**: the record carries everything needed to trip a newsroom alert, whether that's
  `inspection_result == "fail"`, a `score` below a threshold, a closure status, or an establishment
  with repeat fails (group by `establishment_uuid`). A small filter step feeds Slack or email.
- **Tip sheets**: a per-market weekly digest. Filter by `geography.county_fips`, rank by severity,
  and include `result_basis`, `restaurant_name`, and `address`. Chains (the same name across markets)
  and repeat offenders are the recurring story engines.
- **Routing by beat or market**: `county_fips` and `state` map cleanly to a reporter's coverage area.
  The county population enrichment lets you weight how big a deal something is and normalize per
  capita.
- **Depth for investigative work**: the raw and staging layers are retained, so a reporter can drill
  from the headline fail back to the exact violations and the original source record.

## Open questions for USA TODAY (from the brief)

These shape the fuller version and are worth settling early:
- **Warehouse/infra**: is there a home for a medallion warehouse (DuckDB/BigQuery/Snowflake) + dbt
  downstream of raw object storage? That's the obvious next layer.
- **Backfill/history**: do we need to capture *inspection edits over time* (NY only exposes the
  latest inspection; ABQ is weekly)? That argues for append-only history + slowly-changing dimensions.
- **Observability**: is there appetite/support for data-quality monitoring (Monte Carlo / Soda) and
  error tracking (Sentry)?
- **Orchestration**: as source count grows, is there support/experience with Prefect / Dagster /
  Airflow?
- **Presentation**: how far do we take delivery? A raw JSON URL feeding Slack/RSS now, or a queryable
  API or reporter-facing search UI later? What's the demand, and who owns the front end?
