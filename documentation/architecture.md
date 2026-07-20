# Architecture

**Status:** Active · How the pipeline is built and how it scales. *Why* decisions were made lives in
[decisions/](decisions/); source specifics in [sources/](sources/).

## Stages & data flow

```
config/sources.yaml ── the source registry (declare a source here, nothing else hard-codes the list)
        │
        ▼
   EXTRACT ─────────────► data/raw/<source>/        source-native: NY .json · LA .csv×2 · ABQ .pdf/.txt/.json
   (extractors/*)         + drift check (EXPECTED_FIELDS)          ── validation #1: post-extract
        │
        ▼
   TRANSFORM ───────────► data/staging/<source>.json  normalized unified records (JSON)
   (transformers/*)       + pydantic contract per record          ── validation #2: post-transform
        │
        ▼
   LOAD ────────────────► data/production/inspections.json + manifest.json
   (loaders/combine.py)   + JSON Schema gate over the merged set  ── validation #3: pre-load
        │
        ├────────────────► data/errors/   loud plain-text quarantine (any stage)
        └────────────────► data/state/    per-source stage status + metrics
```

Everything after the raw landing zone is JSON conforming to `schema/inspection.schema.json`, which is
**generated from** the authored `schema/inspection_schema.yaml` (`python -m inspections.schema_gen`).

## Module map

| Module | Responsibility |
|---|---|
| `config.py` | load + type `sources.yaml` (the registry) |
| `extractors/` | `base` + one per source; land raw, detect drift |
| `transformers/` | `base` + one per source; raw → unified record dicts |
| `loaders/combine.py` | merge staging → production behind the JSON Schema gate |
| `pipeline.py` | CLI + orchestration (`extract`/`transform`/`load`/`run`) |
| `models.py` | pydantic contract (mirrors the YAML schema) |
| `schema_gen.py` | YAML schema → JSON Schema |
| `enrichment.py` | county FIPS + population (hard-coded, [ADR 0002](decisions/0002-hardcoded-census-enrichment.md)) |
| `ids.py` | deterministic UUIDv5 ([ADR 0007](decisions/0007-deterministic-uuids.md)) |
| `validation.py` | field-drift check · pydantic validation · JSON Schema validation |
| `errors.py` | `ErrorSink` — loud, findable quarantine |
| `state.py` | per-source state file |
| `http.py` | stdlib fetch with transient-vs-permanent retry |
| `logkit.py` | structured (JSON) logging |

## The normalization pattern (how different structures converge)

Each source has an **extractor** (handles its transport: REST / CSV / PDF) and a **transformer**
(maps its native fields to the unified record). They share nothing but the interface and the output
schema. The rest of the system (validation, enrichment, ids, load, delivery) is **source-agnostic**.
So "the same data from differently-structured sources" becomes: *N thin adapters, one shared spine.*

## Adding a source (the scaling story)

1. Add an entry to `config/sources.yaml` (key, extraction method, urls, geo).
2. Add `extractors/<key>.py` (subclass `Extractor`, set `EXPECTED_FIELDS`, land raw).
3. Add `transformers/<key>.py` (subclass `Transformer`, map to the unified record via `assemble()`).
4. Register both in the `extractors/` and `transformers/` `__init__` registries.
5. Add a fixture + a transform test.

No schema change, no pipeline change, no loader change. The 4000+ US jurisdictions that publish
inspections differ only in steps 2–3; everything else is written once. At larger N you'd group
adapters by *shape* (Socrata, ArcGIS/Esri, HealthSpace, Accela, generic-CSV, PDF) so one adapter
serves many jurisdictions by config. That way most "new sources" become a config row, not code.

## Scaling beyond the PoC

- **Storage**: raw → object storage (S3/GCS) instead of git; staging/production → a warehouse
  (DuckDB/Postgres/BigQuery) with medallion layers (bronze/silver/gold) and dbt for the last mile.
- **Orchestration**: the stage chain is modeled on GitHub Actions `workflow_run`; graduate to
  Prefect/Dagster/Airflow when dependencies/backfills/retries outgrow it.
- **Contracts**: the YAML→JSON-Schema contract is the seam a warehouse would enforce as a
  schema/data contract (Great Expectations / Soda) at the silver→gold boundary.

## Breakage handling

Three independent guards, each **loud** and each leaving production intact on failure:
1. **post-extract** — `EXPECTED_FIELDS` drift check catches a source changing shape; that source is
   marked failed and its transform is **skipped** (never normalize known-bad data).
2. **post-transform** — every record runs the pydantic contract; bad records are quarantined, good
   ones proceed. This is the dead-letter method.
3. **pre-load** — JSON Schema gate over the merged set. On any violation the load is **refused** and
   the previous production file is untouched.

Transient vs permanent transport errors are separated in `http.py` (retry 5xx/timeouts; fail fast on
4xx). A non-zero pipeline exit means downstream CI stages don't fire. See
[operations.md](operations.md) for what to do when a guard trips.
