# Architecture

**Status:** Active · How the pipeline is built and how it scales. The reasoning behind each decision
lives in [decisions/](decisions/); source specifics in [sources/](sources/).

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
generated from the authored `schema/inspection_schema.yaml` (`python -m inspections.schema_gen`).

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

Each source has an **extractor** that handles its transport (REST, CSV, or PDF) and a **transformer**
that maps its native fields onto the unified record. The two share nothing but the interface and the
output schema. The rest of the system (validation, enrichment, ids, load, delivery) is
source-agnostic. So "the same data from differently structured sources" comes down to a handful of
thin adapters sitting over one shared spine.

## Adding a source (the scaling story)

1. Add an entry to `config/sources.yaml` (key, extraction method, urls, geo).
2. Add `extractors/<key>.py` (subclass `Extractor`, set `EXPECTED_FIELDS`, land raw).
3. Add `transformers/<key>.py` (subclass `Transformer`, map to the unified record via `assemble()`).
4. Register both in the `extractors/` and `transformers/` `__init__` registries.
5. Add a fixture + a transform test.

No schema change, pipeline change, or loader change is needed. The 4,000-plus US jurisdictions that
publish inspections differ only in steps 2 and 3; everything else is written once. At larger N you
would group adapters by platform *shape* (Socrata, ArcGIS/Esri, HealthSpace, Accela, generic CSV,
PDF) so one adapter serves many jurisdictions from config, and most new sources become a config row
rather than code.

## Scaling beyond the PoC

- **Storage**: raw data moves to object storage (S3/GCS) instead of git; staging and production move
  to a warehouse (DuckDB/Postgres/BigQuery) with medallion layers (bronze/silver/gold) and dbt for
  the last mile.
- **Orchestration**: the stage chain is modeled on GitHub Actions `workflow_run`. Graduate to
  Prefect, Dagster, or Airflow once dependencies, backfills, and retries outgrow it.
- **Contracts**: the YAML-to-JSON-Schema contract is the boundary a warehouse would enforce as a
  schema/data contract (Great Expectations or Soda) at the silver-to-gold step.

## Breakage handling

Three independent guards, each loud and each leaving production intact on failure:
1. **post-extract**: the `EXPECTED_FIELDS` drift check catches a source changing shape. That source is
   marked failed and its transform is skipped, so known-bad data is never normalized.
2. **post-transform**: every record runs through the pydantic contract. Bad records are quarantined
   and good ones proceed (the dead-letter method).
3. **pre-load**: a JSON Schema gate runs over the merged set. On any violation the load is refused and
   the previous production file is left untouched.

Transient and permanent transport errors are separated in `http.py` (retry on 5xx and timeouts, fail
fast on 4xx). A non-zero pipeline exit stops the downstream CI stages from firing. See
[operations.md](operations.md) for what to do when a guard trips.
