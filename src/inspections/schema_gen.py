"""Derive the JSON Schema (draft 2020-12) from the authored YAML schema.

    python -m inspections.schema_gen        # writes schema/inspection.schema.json

The YAML in schema/inspection_schema.yaml is the source of truth; this module is a
pure, deterministic transform of it. Everything downstream of the raw landing zone
is JSON and is validated against the emitted JSON Schema (a core project rule).
"""

from __future__ import annotations

import json
from typing import Any

import yaml

from .paths import SCHEMA_JSON, SCHEMA_YAML

_SCALAR = {
    "string": "string",
    "number": "number",
    "integer": "integer",
    "boolean": "boolean",
}


def _load_yaml() -> dict[str, Any]:
    with SCHEMA_YAML.open() as fh:
        return yaml.safe_load(fh)


def _node(spec: dict[str, Any], enums: dict[str, list[str]]) -> dict[str, Any]:
    """Translate one field/property spec into a JSON Schema node."""
    ftype = spec["type"]
    nullable = bool(spec.get("nullable"))
    out: dict[str, Any]

    if ftype == "enum":
        values = enums[spec["enum"]]
        out = {"type": "string", "enum": list(values)}
    elif ftype in _SCALAR:
        out = {"type": _SCALAR[ftype]}
        if "format" in spec:
            out["format"] = spec["format"]
    elif ftype == "object":
        props = spec.get("properties", {})
        out = {
            "type": "object",
            "additionalProperties": False,
            "properties": {k: _node(v, enums) for k, v in props.items()},
            "required": [k for k, v in props.items() if not v.get("nullable")],
        }
    elif ftype == "array":
        out = {"type": "array", "items": _node(spec["items"], enums)}
    else:  # pragma: no cover - guards against a typo in the YAML
        raise ValueError(f"Unknown field type: {ftype!r}")

    if "description" in spec:
        out["description"] = spec["description"]
    if nullable and "type" in out:
        # Allow null while preserving any `format`/`enum` sibling keywords.
        base_type = out["type"]
        out["type"] = [base_type, "null"] if isinstance(base_type, str) else base_type
    return out


def build_json_schema() -> dict[str, Any]:
    doc = _load_yaml()
    meta = doc["schema"]
    enums = doc["enums"]
    fields = doc["fields"]

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": meta["id"],
        "title": meta["title"],
        "description": (
            f"Generated from schema/inspection_schema.yaml (v{meta['version']}). "
            "Do not edit by hand — run `python -m inspections.schema_gen`."
        ),
        "type": "object",
        "additionalProperties": False,
        "properties": {f["name"]: _node(f, enums) for f in fields},
        "required": [f["name"] for f in fields if f.get("required")],
    }


def write_json_schema() -> None:
    schema = build_json_schema()
    SCHEMA_JSON.write_text(json.dumps(schema, indent=2) + "\n")
    print(f"wrote {SCHEMA_JSON} ({len(schema['properties'])} properties)")


if __name__ == "__main__":
    write_json_schema()
