# Answer Sheet — Multi-Source Inspection Unifier

Addresses the five deliverables in [assignment_instructions.md](../project_scope/assignment_instructions.md).
Working proof-of-concept: `uv run inspections run` produces
[`data/production/inspections.json`](../data/production/inspections.json) from three live sources.
*Why* behind each call lives in [decisions/](decisions/); the build is in [architecture.md](architecture.md).

---

## 1. The three sources & why they're structurally different

Chosen so no two share an extraction shape — the point is to prove one automation absorbs all of them.

| Source | Structure | Extraction challenge | Grain |
|---|---|---|---|
| **New York State** | Socrata SODA **REST API** | the "easy" one: paginate, filter server-side; but data is a *last-inspection snapshot* with violations pre-aggregated into a text blob | 1 row / establishment |
| **Los Angeles County** | two **CSV flat files** on ArcGIS Hub | 24 MB download, **multi-file join** (inspections ⋈ violations on `SERIAL NUMBER`), CP1252 encoding gremlins, program-element grain | 1 row / program / inspection |
| **City of Albuquerque** | weekly **PDF** "Media Report" | **scrape a rolling PDF**: layout parsing, no stable per-row id, no ZIP, summary-vs-detail layers, weekly snapshot (history must be accumulated) | 1 row / inspection / week |

One clean API, one bulk-file join, one PDF scrape — three genuinely different problems. Detail in
[sources/inspection_sources_findings.md](sources/inspection_sources_findings.md).

## 2. Normalizing different structures into one schema

**Pattern: N thin adapters, one shared spine.** Each source has an *extractor* (owns its transport)
and a *transformer* (maps native fields → the unified record). Everything else — validation,
enrichment, id-minting, load, delivery — is written once and is source-agnostic.

The unified record is **one inspection event** with violations nested ([ADR 0006](decisions/0006-record-grain.md)),
defined once in [`schema/inspection_schema.yaml`](../schema/inspection_schema.yaml) and enforced as a
generated JSON Schema + a pydantic model. Key normalization calls:

- **Outcome** — a thin `pass`/`fail`/`unknown` derived by a fixed rule per source, always paired with
  a plain-language `result_basis` ([ADR 0001](decisions/0001-thin-pass-fail-result.md)). NY→
  uncorrected-critical, LA→score<70, ABQ→status. Native `score`/`grade`/counts are carried through so
  the flattening is never lossy. *(This is the deliberate "flatten some edges" the brief anticipated;
  a cross-source risk index is the documented next step.)*
- **Identity** — deterministic UUIDv5 for inspection and establishment ([ADR 0007](decisions/0007-deterministic-uuids.md)),
  so re-runs are idempotent and loads are upserts. Establishment identity is scoped to the source's
  native facility/permit id — no fuzzy entity resolution yet ([ADR 0005](decisions/0005-establishment-identity.md)).
- **Place** — structured `address` ([ADR 0008](decisions/0008-structured-address.md)) + county
  FIPS/GEOID and population, hard-coded for the PoC with a documented Census upgrade path
  ([ADR 0002](decisions/0002-hardcoded-census-enrichment.md)).

Full field-by-field mapping: [data-schemas.md](data-schemas.md).

## 3. Scaling the pattern to many more sources

Adding a source is: **one config row + one extractor + one transformer + a fixture** — no schema,
pipeline, or loader change ([architecture.md → Adding a source](architecture.md#adding-a-source-the-scaling-story)).

The unlock at scale: **group adapters by *shape*, not by jurisdiction.** Thousands of US health
departments run a handful of platforms — Socrata, ArcGIS/Esri, HealthSpace, Accela, generic CSV/Excel,
and PDF. Write one adapter per platform, parameterized by config, and most "new sources" become a
**config entry, not new code**. The registry (`config/sources.yaml`) is the seam that makes coverage a
data problem. Storage/orchestration graduate from git+Actions to object-storage+warehouse(+dbt)+a real
orchestrator (Prefect/Dagster/Airflow) as N grows — the stage boundaries already match that shape.

## 4. Handling breakage (source changes or goes down)

Three independent, **loud**, fail-safe guards — none can silently corrupt production
([architecture.md → Breakage handling](architecture.md#breakage-handling)):

1. **Source changed shape** → post-extract `EXPECTED_FIELDS` drift check; a per-source `fingerprint`
   in state flags it; that source is marked failed and its transform is **skipped**.
2. **Bad records** → post-transform pydantic contract quarantines them to `data/errors/` (dead-letter)
   while good records proceed.
3. **Polluted batch** → pre-load JSON Schema gate **refuses** the load and leaves prior production
   intact.

**Source down** → `http.py` separates transient (5xx/timeout → retry w/ backoff) from permanent (4xx →
fail fast). A stage's non-zero exit stops downstream stages (they trigger on success only), so the last
good production file simply persists until the source recovers. Every failure is a findable plain-text
report in `data/errors/` + a status in `data/state/`. Verified by an automated drift test
(`tests/e2e/test_pipeline.py`). Productionizing this = Great Expectations/Soda at the gate, Sentry on
transport errors, freshness SLAs per source.

## 5. Delivery — surfacing newsworthy signals to reporters

The committed `data/production/inspections.json` is already a delivery endpoint: its **raw GitHub URL**
drops straight into a Slack webhook, an email blast, or (reshaped) an **RSS feed** — no server needed.
On top of that one file:

- **Alerts** — the record has everything to trip a newsroom alert: `inspection_result == "fail"`,
  `score` below a threshold, a closure status, or an establishment with repeat fails (group by
  `establishment_uuid`). A tiny filter step → Slack/email.
- **Tip sheets** — a per-market weekly digest: filter by `geography.county_fips`, rank by severity,
  include `result_basis` + `restaurant_name` + `address`. Chains (same name across markets) and
  repeat offenders are the recurring story engines.
- **Routing by beat/market** — `county_fips`/`state` map cleanly to a reporter's coverage area; the
  county→population enrichment lets you weight "how big a deal is this" and normalize per-capita.
- **Investigative** — the raw + staging layers are retained, so a reporter can drill from the headline
  fail back to the exact violations / source record.

## Open questions for USA TODAY (from the brief)

These shape the "more fleshed-out" version and are worth resolving early:
- **Warehouse/infra** — is there a home for a medallion warehouse (DuckDB/BigQuery/Snowflake) + dbt
  downstream of raw object storage? That's the natural next layer.
- **Backfill/history** — do we need to capture *inspection edits over time* (NY only exposes the latest
  inspection; ABQ is weekly)? That argues for append-only history + slowly-changing dimensions.
- **Observability** — is there appetite/support for data-quality monitoring (Monte Carlo / Soda) and
  error tracking (Sentry)?
- **Orchestration** — as source count grows, is there support/experience with Prefect / Dagster /
  Airflow?
- **Presentation** — how far do we take delivery: raw JSON URL → Slack/RSS now, vs. a queryable API or
  a reporter-facing search UI later? What's the demand and who owns the front end?
