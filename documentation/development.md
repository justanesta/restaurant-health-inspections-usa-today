# Development

**Status:** Active · Local setup, running, testing, debugging.

## Setup

```bash
uv sync --extra dev          # Python 3.12 env + deps (pydantic, pyyaml, jsonschema, pytest, ruff)
sudo apt-get install -y poppler-utils   # provides `pdftotext` for the ABQ extractor (macOS: brew install poppler)
```

Dependencies are intentionally minimal ([tooling.md](../project_scope/tooling.md)): stdlib `urllib`
for HTTP, system `pdftotext` for PDF — no requests/httpx, no Python PDF lib.

## Run

```bash
uv run inspections run                        # all enabled sources, all stages
uv run inspections extract --source albuquerque_city
uv run inspections transform --source new_york_state
uv run inspections load
uv run python -m inspections.schema_gen       # regenerate JSON Schema from the YAML
```

Outputs land under `data/` (`raw/ staging/ production/ errors/ state/`). Point the data root
elsewhere with `INSPECTIONS_DATA_DIR=/some/dir` (tests use this to stay hermetic).

## Test

```bash
uv run pytest -m "not network"     # fast, hermetic (default for CI)
uv run pytest -m network           # opt-in: hits the live NY/LA/ABQ endpoints
uv run ruff check .                # lint
```

Layout: `tests/unit` (pure logic: schema contract, ids, enrichment, result rules, ABQ parser, errors/
state) · `tests/integration` (extractors with mocked transport; per-source transform on fixtures) ·
`tests/e2e` (full pipeline mocked → validated production; a drift scenario; a live smoke test).
Fixtures in `tests/fixtures/` are small, real-shaped payloads.

## Debugging

- **A stage "failed"** — read `data/state/<source>.json` (status + metrics) and the newest
  `data/errors/<stage>__<source>__*.txt` (the human-readable quarantine).
- **Schema drift** — an `extract` error listing missing expected fields means the source changed
  shape; compare the `fingerprint` in state to the previous run, inspect `data/raw/<source>/`.
- **ABQ parsing** — `pdftotext -layout data/raw/albuquerque_city/media_report.pdf - | less`, then
  `parse_summary()` in a REPL. The parser keys off summary rows (`DATE … Pg. N`), so detail-page prose
  is ignored by construction.
- **Validation failure** — the error report shows the field path + message from pydantic/JSON Schema.

## Quality gates (before adding a feature)

Pipeline runs end-to-end · `pytest -m "not network"` green · drift/validation paths exercised ·
`ruff check` clean · schema regenerated & committed · docs/ADRs updated for any schema change.
(`pyright` is specified in the project standards; wire it into CI when the codebase grows.)
