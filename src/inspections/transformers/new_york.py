"""New York State transformer: SODA JSON -> unified records.

Result rule (ADR 0001): fail if any critical violation was NOT corrected on site
(`total_crit_not_corrected` > 0), else pass. The raw `violations` text blob is split
into individual items; NY only publishes aggregate critical/non-critical counts, so
per-item criticality is left null.
"""

from __future__ import annotations

import json
import re
from typing import Any

from ..enrichment import load_geo_reference
from .base import Transformer, iso_prefix

_ITEM_SPLIT = re.compile(r"(?=Item\s+\d)")


def _to_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def split_violations(text: str | None) -> list[dict[str, Any]]:
    text = (text or "").strip()
    if not text:
        return []
    parts = [p.strip() for p in _ITEM_SPLIT.split(text) if p.strip()]
    return [{"description": p} for p in (parts or [text])]


class NewYorkStateTransformer(Transformer):
    def transform(self) -> list[dict[str, Any]]:
        records = json.loads((self.raw_dir / "inspections.json").read_text())
        geo_ref = load_geo_reference()
        state_fips = self.source.geo.state_fips or "36"
        out: list[dict[str, Any]] = []

        for rec in records:
            op_id = (rec.get("nys_health_operation_id") or "").strip()
            date_raw = rec.get("date")
            if not op_id or not date_raw:
                continue  # unusable key -> the pipeline's validation will also catch/omit it
            date = iso_prefix(date_raw)

            crit = _to_int(rec.get("total_critical_violations"))
            crit_nc = _to_int(rec.get("total_crit_not_corrected"))
            noncrit = _to_int(rec.get("total_noncritical_violations"))
            result = "fail" if crit_nc > 0 else "pass"
            basis = (
                f"critical_not_corrected={crit_nc}, critical={crit}, noncritical={noncrit} "
                f"-> {'fail (uncorrected critical)' if result == 'fail' else 'pass'}"
            )

            out.append(self.assemble(
                source_inspection_id=f"{op_id}|{date}",
                source_establishment_id=op_id,
                restaurant_name=(rec.get("facility") or rec.get("operation_name") or "").strip(),
                address={
                    "street": (rec.get("facility_address") or "").strip() or None,
                    "city": (rec.get("city") or "").strip() or None,
                    "state": (rec.get("food_service_facility_state") or "NY").strip() or None,
                    "postal_code": (rec.get("zip_code") or "").strip() or None,
                },
                inspection_date=date,
                inspection_type=(rec.get("inspection_type") or "").strip() or None,
                result=result,
                result_basis=basis,
                critical_violation_count=crit,
                total_violation_count=crit + noncrit,
                violations=split_violations(rec.get("violations")),
                geography=geo_ref.by_county_name(rec.get("county"), state_fips),
            ))
        return out
