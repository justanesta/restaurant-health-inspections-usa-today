# 0005 — Establishment identity via source id only (no entity resolution)

**Status:** Accepted (2026-07-18)

## Context
Establishments get inspected repeatedly and can change names/owners over time; the same physical
place may even appear under different ids. True cross-record identity is an entity-resolution problem.
Usefully, all three sources *do* carry a native facility/permit id (NY `nys_health_operation_id`,
LA `FACILITY ID`, ABQ permit #).

## Decision
Key each establishment by **its source's native facility/permit id** via a deterministic
`establishment_uuid` ([0007](0007-deterministic-uuids.md)). No fuzzy matching, no cross-source linking.

## Consequences
- Reliable grouping of repeat inspections of the same place *within a source* (verified: 17 such
  groups in the committed slice).
- **Not** handled: the same place under a changed id, renames, or the same chain across sources. A
  record's identity is scoped to `(source, native id)`.
- Upgrade path: an entity-resolution stage (address+name normalization/blocking) assigning a stable
  cross-source `establishment_uuid` — deferred. This ADR is superseded when that lands.
