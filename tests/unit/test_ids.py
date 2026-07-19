"""Deterministic, namespaced UUIDs."""

from __future__ import annotations

import uuid

from inspections.ids import establishment_uuid, inspection_uuid


def test_inspection_uuid_is_deterministic():
    a = inspection_uuid("new_york_state", "111|2026-06-01")
    b = inspection_uuid("new_york_state", "111|2026-06-01")
    assert a == b
    assert uuid.UUID(a).version == 5


def test_natural_key_changes_uuid():
    assert inspection_uuid("new_york_state", "111") != inspection_uuid("new_york_state", "222")


def test_source_namespaces_are_distinct():
    assert inspection_uuid("new_york_state", "1") != inspection_uuid("los_angeles_county", "1")


def test_inspection_and_establishment_uuids_differ():
    assert inspection_uuid("s", "k") != establishment_uuid("s", "k")
