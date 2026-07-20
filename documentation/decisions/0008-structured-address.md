# 0008 — Structured address object over a flat string

**Status:** Accepted (2026-07-18)

## Context
The initial data model typed `restaurant_address` as a single string and, for NY, mapped it to a
field that already jams street and city together (`"22 MAIN STREET,  RANDOLPH"`). All three sources
actually expose address components separately (NY has `facility_address` / `city` / `zip_code`; LA has
ADDRESS/CITY/STATE/ZIP; ABQ has a street line, with city = Albuquerque implied and no ZIP).

## Decision
Model `address` as a **structured object** `{ street, city, state, postal_code }`, each nullable.
Populate components from the source's separate fields rather than from a pre-concatenated string.

## Consequences
- Downstream consumers can filter and group by city/state/ZIP without re-parsing a string, and
  geocoding (the enrichment upgrade path) has clean inputs.
- Gaps are explicit: ABQ `postal_code` is `null` (the summary carries no ZIP) rather than guessed.
- This deviates from the draft's flat string, an improvement recorded here so the mapping in
  `data-schemas.md` and `schema/inspection_schema.yaml` stays the single source of truth.
