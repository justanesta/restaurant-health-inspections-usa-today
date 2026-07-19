"""Validation used at every stage boundary.

  * post-extract : check_expected_fields() detects upstream schema drift (missing columns)
  * post-transform: validate_records() runs each record through the pydantic contract
  * pre-load     : json_schema_errors() validates the JSON against the derived JSON Schema

Failures are returned, never raised past the caller, so the caller can route them to an
ErrorSink and keep going.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Iterable

import jsonschema
from pydantic import ValidationError

from .models import Inspection
from .paths import SCHEMA_JSON
from .schema_gen import build_json_schema


def check_expected_fields(present: Iterable[str], expected: Iterable[str]) -> list[str]:
    """Return expected field names that are missing from `present` (upstream drift)."""
    have = set(present)
    return [f for f in expected if f not in have]


def validate_records(
    records: list[dict[str, Any]],
) -> tuple[list[Inspection], list[tuple[int, str]]]:
    """Split records into (valid pydantic models, [(index, error message)])."""
    valid: list[Inspection] = []
    errors: list[tuple[int, str]] = []
    for i, rec in enumerate(records):
        try:
            valid.append(Inspection.model_validate(rec))
        except ValidationError as exc:
            errors.append((i, _terse(exc)))
    return valid, errors


@lru_cache(maxsize=1)
def _schema() -> dict[str, Any]:
    if SCHEMA_JSON.exists():
        return json.loads(SCHEMA_JSON.read_text())
    return build_json_schema()


def json_schema_errors(records: list[dict[str, Any]]) -> list[tuple[int, str]]:
    """Validate JSON-native dicts against the derived JSON Schema."""
    validator = jsonschema.Draft202012Validator(_schema())
    out: list[tuple[int, str]] = []
    for i, rec in enumerate(records):
        for err in validator.iter_errors(rec):
            path = "/".join(str(p) for p in err.path) or "<root>"
            out.append((i, f"{path}: {err.message}"))
    return out


def _terse(exc: ValidationError) -> str:
    parts = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err["loc"])
        parts.append(f"{loc}: {err['msg']}")
    return "; ".join(parts)
