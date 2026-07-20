# Data Schemas

**Status:** Active · The unified record, per-source field mappings, and validation rules.
The single source of truth is [`schema/inspection_schema.yaml`](../schema/inspection_schema.yaml);
this doc explains it. The machine contract `schema/inspection.schema.json` is generated from it.

## The unified record (one inspection event, [ADR 0006](decisions/0006-record-grain.md))

| Field | Type | Notes |
|---|---|---|
| `schema_version` | string | semver of the schema this record conforms to |
| `inspection_uuid` | uuid | deterministic; PK ([ADR 0007](decisions/0007-deterministic-uuids.md)) |
| `establishment_uuid` | uuid | deterministic; groups a place's inspections ([ADR 0005](decisions/0005-establishment-identity.md)) |
| `source` | enum | `new_york_state` · `los_angeles_county` · `albuquerque_city` |
| `source_inspection_id` | string | native (or composed) inspection id |
| `source_establishment_id` | string? | native facility/permit id |
| `restaurant_name` | string | |
| `address` | object | `{street, city, state, postal_code}`, each nullable ([ADR 0008](decisions/0008-structured-address.md)) |
| `inspection_date` | date | ISO-8601 |
| `inspection_type` | string? | source-native service/type |
| `inspection_result` | enum | `pass`/`fail`/`unknown` ([ADR 0001](decisions/0001-thin-pass-fail-result.md)) |
| `result_basis` | string | plain-language derivation (transparency) |
| `score` | number? | LA only (0–100) |
| `grade` | string? | LA only (A/B/C) |
| `critical_violation_count` | int? | null where source can't distinguish |
| `total_violation_count` | int? | null where unknown (e.g. ABQ) |
| `violations` | array | `{description, code?, status?, points?, is_critical?}`; may be empty |
| `geography` | object | county name/FIPS/state + population snapshot + `enrichment_note` |
| `source_metadata` | object | provenance: source name, publisher, url, method, dataset id, `extracted_at` |
| `ingested_at` | datetime | when the transform produced this record (UTC) |

`source_metadata` repeats a few per-source constants (name, publisher, url, method, dataset id) on
every record. That redundancy is on purpose: a single inspection stays self-describing and citable on
its own (say, dropped into a Slack alert or an RSS item) without a join back to the manifest.

## Per-source field mapping

The authoritative mapping (with derivation formulas) is the `source_mappings:` block in the schema
YAML. Summary:

| Unified | New York (SODA json) | Los Angeles (CSV) | Albuquerque (PDF summary) |
|---|---|---|---|
| `restaurant_name` | `facility` | `FACILITY NAME` | header, text before ` - ` |
| `address.street` | `facility_address` | `FACILITY ADDRESS` | header, text after ` - ` |
| `address.city` | `city` | `FACILITY CITY` | `Albuquerque` (const) |
| `address.state` | `food_service_facility_state` | `FACILITY STATE` | `NM` (const) |
| `address.postal_code` | `zip_code` | `FACILITY ZIP` | `null` (not in summary) |
| `inspection_date` | `date` (ISO) | `ACTIVITY DATE` (m/d/Y) | `Inspection Date` (m/d/Y) |
| `inspection_type` | `inspection_type` | `SERVICE DESCRIPTION` | `Inspection Type` |
| `source_inspection_id` | `nys_health_operation_id\|date` | `SERIAL NUMBER` | `permit\|date\|inspection_id` |
| `source_establishment_id` | `nys_health_operation_id` | `FACILITY ID` | permit # |
| `inspection_result` | crit-not-corrected > 0 → fail | `SCORE` < 70 → fail | status unsat/closure/closed → fail |
| `score` / `grade` | — / — | `SCORE` / `GRADE` | — / — |
| `critical_violation_count` | `total_critical_violations` | count(points ≥ 4) | — |
| `total_violation_count` | crit + noncrit | count(joined rows) | — |
| `violations[]` | `violations` blob, split on `Item` | join on `SERIAL NUMBER` | `[]` ([ADR 0004](decisions/0004-albuquerque-summary-only.md)) |
| `geography` | by `county` name → FIPS | const `06037` | const `35001` |

Notes: LA `is_critical` uses a documented heuristic (point deduction ≥ 4). NY only publishes
aggregate counts, so per-item `is_critical` is null.

## Validation rules (three gates)

1. **post-extract**: are the `EXPECTED_FIELDS` present? Missing fields mean upstream drift, so the
   source is marked failed and its transform is skipped.
2. **post-transform**: each record satisfies the pydantic `Inspection` model (`extra="forbid"`, plus
   types, enums, and required fields). Failures are quarantined to `data/errors/`; valid records
   continue.
3. **pre-load**: the merged set validates against `inspection.schema.json`. Any violation refuses the
   load and leaves production untouched.

## Evolving the schema

Edit `schema/inspection_schema.yaml`, run `python -m inspections.schema_gen`, then update `models.py`
to match. `tests/unit/test_schema_contract.py` fails if the YAML, the pydantic model, and the
committed JSON Schema disagree, so they can't silently drift.
