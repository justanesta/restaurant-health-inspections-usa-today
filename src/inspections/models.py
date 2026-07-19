"""Pydantic runtime contract for a unified inspection record.

These models MIRROR schema/inspection_schema.yaml (the authored source of truth).
They are the runtime validator used at every stage boundary. A contract test
(tests/unit/test_schema_contract.py) asserts field-name + required parity with the
YAML so the two cannot silently drift.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Source(str, Enum):
    new_york_state = "new_york_state"
    los_angeles_county = "los_angeles_county"
    albuquerque_city = "albuquerque_city"


class ExtractionMethod(str, Enum):
    api = "api"
    flat_file = "flat_file"
    pdf = "pdf"


class InspectionResult(str, Enum):
    passed = "pass"          # `pass` is a Python keyword; value is still the string "pass"
    failed = "fail"
    unknown = "unknown"


class _Model(BaseModel):
    # Reject unknown keys so an upstream schema change surfaces loudly instead of
    # being silently dropped (a core project requirement).
    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class Address(_Model):
    street: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None


class Violation(_Model):
    description: str
    code: str | None = None
    status: str | None = None
    points: float | None = None
    is_critical: bool | None = None


class Geography(_Model):
    county_name: str | None = None
    county_fips: str | None = None
    state_fips: str | None = None
    state: str | None = None
    population: int | None = None
    population_vintage: str | None = None
    enrichment_note: str | None = None


class SourceMetadata(_Model):
    source_name: str
    publisher: str | None = None
    landing_url: str | None = None
    extraction_method: ExtractionMethod
    source_dataset_id: str | None = None
    extracted_at: datetime | None = None


class Inspection(_Model):
    """One normalized inspection event — the unit of the production dataset."""

    schema_version: str
    inspection_uuid: str
    establishment_uuid: str
    source: Source
    source_inspection_id: str
    source_establishment_id: str | None = None
    restaurant_name: str
    address: Address
    inspection_date: date
    inspection_type: str | None = None
    inspection_result: InspectionResult
    result_basis: str
    score: float | None = None
    grade: str | None = None
    critical_violation_count: int | None = None
    total_violation_count: int | None = None
    violations: list[Violation] = Field(default_factory=list)
    geography: Geography
    source_metadata: SourceMetadata
    ingested_at: datetime
