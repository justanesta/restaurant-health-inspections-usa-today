"""Los Angeles County transformer: two CSVs -> unified records.

Joins the violations file to each inspection on SERIAL NUMBER. Result rule (ADR 0001):
fail if SCORE < 70, else pass (LA also publishes a letter GRADE, carried through). Per-
violation criticality uses a documented heuristic: LA deducts more points for the most
serious findings, so points >= 4 is flagged critical.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from typing import Any

from ..enrichment import load_geo_reference
from .base import Transformer, us_date_to_iso

_CRITICAL_POINTS = 4.0  # LA point deductions: 1 / 2 / 4; treat the 4-pt band as critical


def _to_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _read(path) -> list[dict[str, str]]:
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


class LosAngelesCountyTransformer(Transformer):
    def transform(self) -> list[dict[str, Any]]:
        inspections = _read(self.raw_dir / "inspections.csv")
        violations = _read(self.raw_dir / "violations.csv")

        by_serial: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for v in violations:
            points = _to_float(v.get("POINTS"))
            by_serial[v.get("SERIAL NUMBER", "")].append({
                "code": (v.get("VIOLATION CODE") or "").strip() or None,
                "description": (v.get("VIOLATION DESCRIPTION") or "").strip(),
                "status": (v.get("VIOLATION STATUS") or "").strip() or None,
                "points": points,
                "is_critical": (points is not None and points >= _CRITICAL_POINTS),
            })

        geo = load_geo_reference().by_fips(self.source.geo.county_fips or "06037")
        out: list[dict[str, Any]] = []

        for row in inspections:
            serial = (row.get("SERIAL NUMBER") or "").strip()
            if not serial or not row.get("ACTIVITY DATE"):
                continue
            score = _to_float(row.get("SCORE"))
            vios = by_serial.get(serial, [])
            if score is None:
                result, basis = "unknown", "no SCORE published"
            elif score < 70:
                result, basis = "fail", f"score={score:g} (<70 fails)"
            else:
                result, basis = "pass", f"score={score:g} (>=70 passes)"

            out.append(self.assemble(
                source_inspection_id=serial,
                source_establishment_id=(row.get("FACILITY ID") or "").strip() or None,
                restaurant_name=(row.get("FACILITY NAME") or "").strip(),
                address={
                    "street": (row.get("FACILITY ADDRESS") or "").strip() or None,
                    "city": (row.get("FACILITY CITY") or "").strip() or None,
                    "state": (row.get("FACILITY STATE") or "").strip() or None,
                    "postal_code": (row.get("FACILITY ZIP") or "").strip() or None,
                },
                inspection_date=us_date_to_iso(row["ACTIVITY DATE"]),
                inspection_type=(row.get("SERVICE DESCRIPTION") or "").strip() or None,
                result=result,
                result_basis=basis,
                score=score,
                grade=(row.get("GRADE") or "").strip() or None,
                critical_violation_count=sum(1 for v in vios if v["is_critical"]),
                total_violation_count=len(vios),
                violations=vios,
                geography=dict(geo),
            ))
        return out
