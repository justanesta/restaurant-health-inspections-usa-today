# Operations

**Status:** Active · Scheduling, monitoring, troubleshooting, knobs.

## Scheduling (GitHub Actions)

Three chained workflows in `.github/workflows/`, each committing its stage output back to the repo
(the PoC's "storage layer"):

```
extract.yml  (cron weekly + workflow_dispatch)  ──success──▶  transform.yml (workflow_run)  ──success──▶  load.yml (workflow_run)
```

- Later stages fire **only on the previous one's success** (`workflow_run` + a `conclusion == 'success'`
  gate), so bad data never propagates.
- Any stage is independently re-runnable via **workflow_dispatch**; `extract` takes an optional
  `source` input.
- `ci.yml` runs lint + the hermetic test suite on every push/PR (and fails if the committed JSON
  Schema is stale).

Cadence note: the single weekly cron matches ABQ (weekly). NY refreshes monthly and LA quarterly — a
real deploy would split per-source schedules (or a matrix) rather than re-pull everything weekly.

## Knobs (`config/sources.yaml`)

| Knob | Effect |
|---|---|
| `window_days` (90) | recency window (NY by `date`, LA by `ACTIVITY DATE`; ABQ = 1 week) |
| `sample_limit` (400) | per-source cap for the committed slice; `null` = full pull |
| `sources[].enabled` | turn a source on/off |

For a full backfill: `sample_limit: null`, raise `window_days`, and move the raw layer out of git
(see [architecture.md](architecture.md) "Scaling").

## Monitoring

- **Per-source health**: `data/state/<source>.json` — last status per stage, record counts, the source
  `fingerprint`, error counts, and the window used. `data/production/manifest.json` — totals,
  per-source counts, pass/fail breakdown, and each source's extract state.
- **Logs**: structured JSON lines on stderr (`event`, `source`, counts, `status`) — greppable and
  ready to ship to CloudWatch/Datadog.
- **Where a real deploy would add observability**: data-quality monitors (Great Expectations / Soda)
  at the pre-load gate; error tracking (Sentry) around extractor/transport failures; freshness SLAs
  per source keyed off `state.updated_at`.

## Troubleshooting

| Symptom | Look at | Likely cause / action |
|---|---|---|
| stage exit code 1 | newest `data/errors/*.txt` + `data/state/*.json` | drift / validation / load-refusal; details in the report |
| `extract` lists missing fields | `data/raw/<source>/`, `fingerprint` vs last run | source changed shape → fix the extractor's `EXPECTED_FIELDS`/mapping |
| `load.refused` | `data/errors/load__combined__*.txt` | a record failed the JSON Schema gate; production left intact |
| ABQ record_count = 0 | `pdftotext` installed? report layout changed? | reinstall poppler; re-inspect the summary layout |
| population null on many rows | `config/geo_reference.yaml` | expected for non-headline counties ([ADR 0002](decisions/0002-hardcoded-census-enrichment.md)); refresh via `scripts/build_geo_reference.py` |

## Idempotency & re-runs

Re-running is safe — ids and business content are stable ([ADR 0007](decisions/0007-deterministic-uuids.md)).
`ingested_at`/`extracted_at` timestamps do change each run, so a re-run produces a small git diff even
when nothing substantive changed. That's expected; the manifest's counts/breakdown are the real "did
anything change?" signal.
