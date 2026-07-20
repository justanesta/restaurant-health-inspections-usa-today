# Development

**Status:** Active · Local setup, running, testing, debugging.

## Setup

```bash
uv sync --extra dev          # Python 3.12 env + deps (pydantic, pyyaml, jsonschema, pytest, ruff)
sudo apt-get install -y poppler-utils   # provides `pdftotext` for the ABQ extractor (macOS: brew install poppler)
```

Dependencies are kept minimal ([tooling.md](../project_scope/tooling.md)): stdlib `urllib` for HTTP
and system `pdftotext` for PDF, with no requests/httpx and no Python PDF library.

## Run

```bash
uv run inspections run                        # all enabled sources, all stages
uv run inspections extract --source albuquerque_city
uv run inspections transform --source new_york_state
uv run inspections load
uv run python -m inspections.schema_gen       # regenerate JSON Schema from the YAML
```

Outputs land under `data/` (`raw/ staging/ production/ errors/ state/`). Point the data root
somewhere else with `INSPECTIONS_DATA_DIR=/some/dir` (the tests use this to stay hermetic).

## Test

```bash
uv run pytest -m "not network"     # fast, hermetic (default for CI)
uv run pytest -m network           # opt-in: hits the live NY/LA/ABQ endpoints
uv run ruff check .                # lint
```

Layout: `tests/unit` covers pure logic (schema contract, ids, enrichment, result rules, the ABQ
parser, errors/state); `tests/integration` covers extractors with mocked transport and per-source
transforms on fixtures; `tests/e2e` runs the full pipeline mocked through to validated production,
plus a drift scenario and a live smoke test. Fixtures in `tests/fixtures/` are small, real-shaped
payloads.

## Debugging

- **A stage failed**: read `data/state/<source>.json` (status and metrics) and the newest
  `data/errors/<stage>__<source>__*.txt` (the human-readable quarantine).
- **Schema drift**: an `extract` error listing missing expected fields means the source changed
  shape. Compare the `fingerprint` in state to the previous run and inspect `data/raw/<source>/`.
- **ABQ parsing**: run `pdftotext -layout data/raw/albuquerque_city/media_report.pdf - | less`, then
  `parse_summary()` in a REPL. The parser keys off summary rows (`DATE … Pg. N`), so detail-page
  prose is ignored by construction.
- **Validation failure**: the error report shows the field path and message from pydantic or JSON
  Schema.

## Quality gates (before adding a feature)

- Pipeline runs end-to-end
- `pytest -m "not network"` is green
- drift and validation paths are exercised
- `ruff check` is clean
- the schema is regenerated and committed
- docs and ADRs are updated for any schema change

`pyright` is specified in the project standards; wire it into CI as the codebase grows.
