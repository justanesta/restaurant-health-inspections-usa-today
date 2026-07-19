"""The pydantic model, the authored YAML, and the committed JSON Schema must agree."""

from __future__ import annotations

import json

import jsonschema
import yaml

from inspections.models import ExtractionMethod, InspectionResult, Inspection, Source
from inspections.paths import SCHEMA_JSON, SCHEMA_YAML
from inspections.schema_gen import build_json_schema


def _yaml():
    return yaml.safe_load(SCHEMA_YAML.read_text())


def test_field_name_parity():
    yaml_fields = {f["name"] for f in _yaml()["fields"]}
    model_fields = set(Inspection.model_fields)
    assert yaml_fields == model_fields, yaml_fields ^ model_fields


def test_enum_value_parity():
    enums = _yaml()["enums"]
    assert {e.value for e in Source} == set(enums["source"])
    assert {e.value for e in ExtractionMethod} == set(enums["extraction_method"])
    assert {e.value for e in InspectionResult} == set(enums["inspection_result"])


def test_generated_schema_is_valid_draft2020():
    jsonschema.Draft202012Validator.check_schema(build_json_schema())


def test_committed_schema_is_up_to_date():
    """schema/inspection.schema.json must equal `schema_gen` output (run it after edits)."""
    on_disk = json.loads(SCHEMA_JSON.read_text())
    assert on_disk == build_json_schema(), "stale schema — run `python -m inspections.schema_gen`"


def test_required_fields_are_a_subset_of_model_fields():
    required = {f["name"] for f in _yaml()["fields"] if f.get("required")}
    assert required <= set(Inspection.model_fields)
