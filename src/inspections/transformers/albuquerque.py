"""City of Albuquerque transformer: parsed summary rows -> unified records.

Result rule (ADR 0001): fail if the inspection status signals a closure/unsatisfactory
outcome OR the establishment's operational status is Closed; else pass. This fixes the
original draft rule (which treated only 'Closed' as failure and would have passed an
'Unsatisfactory Re-Inspection required'). Violations are empty by design (summary-only,
ADR 0004).
"""

from __future__ import annotations

import json
from typing import Any

from ..enrichment import load_geo_reference
from .base import Transformer, us_date_to_iso

_FAIL_STATUS_MARKERS = ("unsatisfactory", "closure", "closed")


def derive_result(inspection_status: str, operational_status: str) -> tuple[str, str]:
    status = (inspection_status or "").strip()
    op = (operational_status or "").strip()
    fail = any(m in status.lower() for m in _FAIL_STATUS_MARKERS) or op.lower() == "closed"
    result = "fail" if fail else "pass"
    return result, f"status={status!r}; operational_status={op!r} -> {result}"


class AlbuquerqueCityTransformer(Transformer):
    def transform(self) -> list[dict[str, Any]]:
        rows = json.loads((self.raw_dir / "summary.json").read_text())
        geo = load_geo_reference().by_fips(self.source.geo.county_fips or "35001")
        state = self.source.geo.state or "NM"
        out: list[dict[str, Any]] = []

        for row in rows:
            permit = (row.get("permit") or "").strip()
            date_raw = row.get("inspection_date")
            insp_id = (row.get("inspection_id") or "").strip()
            if not date_raw or not (permit or insp_id):
                continue
            date = us_date_to_iso(date_raw)
            result, basis = derive_result(row.get("inspection_status", ""), row.get("operational_status", ""))

            out.append(self.assemble(
                # ABQ's Inspection ID is not always unique (sometimes it's just the permit #),
                # so the natural key is composite.
                source_inspection_id=f"{permit}|{date}|{insp_id}",
                source_establishment_id=permit or None,
                restaurant_name=(row.get("establishment_name") or "").strip(),
                address={
                    "street": (row.get("address") or "").strip() or None,
                    "city": "Albuquerque",
                    "state": state,
                    "postal_code": None,  # summary table carries no ZIP
                },
                inspection_date=date,
                inspection_type=(row.get("inspection_type") or "").strip() or None,
                result=result,
                result_basis=basis,
                violations=[],
                geography=dict(geo),
            ))
        return out
