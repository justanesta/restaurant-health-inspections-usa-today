# Architectural Decision Records

Each ADR captures one decision: its context, the call, and the consequences. Code and schema
reference these by number (e.g. `ADR 0001`). To supersede an ADR, add a new one and mark the old one
Superseded; never silently rewrite.

| # | Decision | Status |
|---|---|---|
| [0001](0001-thin-pass-fail-result.md) | Thin pass/fail with fixed per-source rules | Accepted |
| [0002](0002-hardcoded-census-enrichment.md) | Hard-code county FIPS + population (no live Census API) | Accepted |
| [0003](0003-bounded-recent-slice.md) | Bounded recent data slice for the PoC | Accepted |
| [0004](0004-albuquerque-summary-only.md) | Albuquerque: parse the summary table only | Accepted |
| [0005](0005-establishment-identity.md) | Establishment identity via source id only (no entity resolution) | Accepted |
| [0006](0006-record-grain.md) | Record grain = one inspection event, violations nested | Accepted |
| [0007](0007-deterministic-uuids.md) | Deterministic UUIDv5 keys for idempotency | Accepted |
| [0008](0008-structured-address.md) | Structured address object over a flat string | Accepted |
