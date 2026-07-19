# 0003 — Bounded recent data slice for the PoC

**Status:** Accepted (2026-07-18)

## Context
LA's inspections CSV alone is ~24 MB (3 years); NY is a ~21.5k-row snapshot; ABQ is one week.
Committing full history to git on every run would bloat the repo and slow CI, and adds nothing to a
proof of *approach*.

## Decision
Pull a **bounded recent slice**, controlled in `config/sources.yaml`:
- `window_days` (default 90) — NY filtered by `date`, LA by `ACTIVITY DATE`; ABQ is inherently one week.
- `sample_limit` (default 400/source) — caps the committed demo so the repo stays light.
Both are one-line changes; `sample_limit: null` + a larger `window_days` gives a full pull.

## Consequences
- The committed `data/` slice is small, real, and diffable; CI is fast.
- LA extraction still downloads the whole CSV then filters client-side (the source notes point at the
  `/data` item). Production would filter **server-side** via the ArcGIS Feature Service query API
  (`where=ACTIVITY_DATE > …`) — noted in `los_angeles.py` and architecture.md.
- NY's dataset is "last inspection per establishment", so its window is a moving snapshot, not history
  (see [0006](0006-record-grain.md)).
