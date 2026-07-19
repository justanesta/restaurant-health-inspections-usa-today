# 0006 — Record grain = one inspection event, violations nested

**Status:** Accepted (2026-07-18)

## Context
The sources land at three different grains: NY = one row per **establishment** (its last inspection),
violations pre-aggregated into a text blob + counts; LA = one row per **program-element per
inspection**, with violations in a **separate file** (1 inspection → many violation rows); ABQ = one
row per **inspection** in the weekly report. "One inspection" therefore means three different things.

## Decision
The unified record grain is **one inspection event**. Violations are a **nested array** on the record
(not separate rows). The establishment is a separate identity carried via `establishment_uuid`
([0005](0005-establishment-identity.md)), denormalized onto each inspection for convenience.

## Consequences
- One record shape regardless of how the source models violations: NY's blob is split into items,
  LA's joined child rows are nested, ABQ's is empty.
- LA's program-element rows are preserved as distinct inspections (each has its own `SERIAL NUMBER`);
  we do **not** collapse a facility's programs into one. That matches how LA issues scores.
- A warehouse would likely explode `violations` into a child table downstream; the nested-JSON form
  is the right shape for a file-based, document-oriented production artifact.
