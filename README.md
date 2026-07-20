# Restaurant Health Inspections — multi-source unifier (PoC)

A proof-of-concept that pulls the **same** restaurant-inspection fields out of three
**structurally different** government sources and normalizes them into **one schema**.

It's meant to work through a design question rather than ship a finished product: how do you
collect one consistent set of fields from sources that share no common structure, and do it as a
single repeatable automation instead of a pile of one-off scripts? The reasoning behind the schema
trade-offs, scaling, breakage handling, and delivery to reporters lives in
[`documentation/`](documentation/) and the [answer sheet](documentation/answer_sheet.md).

## The three sources

Each source was picked for a different structural challenge, so no two share an extraction shape.

| Source | Structure | Extraction | Grain | Violations |
|---|---|---|---|---|
| **New York State** | Clean REST API (Socrata SODA) | `api` | 1 row = an establishment's *last* inspection | pre-aggregated text + counts |
| **Los Angeles County** | Two downloadable CSV flat files | `flat_file` | 1 row = a program-element per inspection | separate file, joined on `SERIAL NUMBER` |
| **City of Albuquerque** | Weekly PDF "Media Report" | `pdf` | 1 row = an inspection in the current week | (summary-only in this PoC) |

New York is a clean API, LA a multi-file CSV join, Albuquerque a rolling PDF scrape. Each is a
different extraction problem, and all three produce the same output record.

## Data flow

```
                 config/sources.yaml  (the source registry — the one place sources are declared)
                          │
   ┌──────────────────────┼───────────────────────┐
   ▼                      ▼                        ▼
extract ─► data/raw/    transform ─► data/staging/   load ─► data/production/
(source-native:         (normalized per-source        (combined, validated
 json / csv / pdf+text)  JSON, schema-validated)        JSON: inspections.json)
   │                      │                              │
   └── validate on extract (detect upstream drift)       └── validate before load (block downstream pollution)
                          │
                 data/errors/  (loud plain-text quarantine)   data/state/  (per-source run state)
```

Everything after the raw landing zone is **JSON conforming to a JSON Schema**
(`schema/inspection.schema.json`), which is generated from the authored
[`schema/inspection_schema.yaml`](schema/inspection_schema.yaml).

## Quickstart

```bash
uv sync --extra dev                      # create env (Python 3.12) + install deps
uv run python -m inspections.schema_gen  # (re)derive the JSON Schema from the YAML

# Run the whole pipeline for all enabled sources (bounded recent slice):
uv run inspections run

# Or a single stage / single source:
uv run inspections extract   --source new_york_state
uv run inspections transform --source los_angeles_county
uv run inspections load

uv run pytest                # unit + integration + e2e (add -m 'not network' to skip live calls)
```

Output lands in `data/production/inspections.json`. A small, real bounded slice is
committed so you can see end-to-end output without running anything.

## What's here

```
config/        sources.yaml (source registry) + geo_reference.yaml (hard-coded FIPS/pop)
schema/        inspection_schema.yaml (authored) -> inspection.schema.json (generated)
src/inspections/
  extractors/  one per source (new_york, los_angeles, albuquerque) + base
  transformers/one per source -> unified records + base
  loaders/     combine.py (merge staging -> validated production)
  pipeline.py  orchestration CLI      ids.py enrichment.py errors.py state.py validation.py
data/          raw/ staging/ production/ errors/ state/
documentation/ architecture · data-schemas · development · operations · decisions/ (ADRs) · answer_sheet
.github/workflows/  extract -> transform -> load (scheduled + manual)
```

## Design decisions & scope

The scope is small on purpose. Four scoping calls shape it: Albuquerque summary-only, county-level
hard-coded Census enrichment, a bounded recent data slice, and a thin pass/fail result model. Each
is written up as an **ADR** in [`documentation/decisions/`](documentation/decisions/). Start there
and with the [answer sheet](documentation/answer_sheet.md) for why it looks the way it does.
