# 0007 — Deterministic UUIDv5 keys for idempotency

**Status:** Accepted (2026-07-18)

## Context
The pipeline must be safe to re-run (idempotent): re-processing the same source data must not create
duplicates, and a load into a warehouse should be an upsert. Random UUIDs or DB sequences break that.

## Decision
Both ids are **deterministic UUIDv5** over a fixed project namespace:
- `inspection_uuid = uuid5(ns, "inspection|<source>|<natural key>")`
- `establishment_uuid = uuid5(ns, "establishment|<source>|<facility/permit id>")`

Natural keys are chosen to be unique within a source: NY `operation_id|date`, LA `SERIAL NUMBER`, ABQ
`permit|date|inspection_id` (ABQ's inspection id alone isn't always unique, sometimes it's just the
permit #, so the key is composite).

## Consequences
- Re-running yields **identical** ids and business content (verified: same uuid set, zero duplicates,
  zero business-content diffs across re-runs). Only the `ingested_at`/`extracted_at` timestamps change,
  by design; they record when *this* run happened and are metadata, not identity.
- Loads are upsert-ready: key on `inspection_uuid`.
- Because timestamps churn, a committed re-run produces a small git diff even when data is unchanged.
  That's acceptable for a PoC (documented in operations.md).
