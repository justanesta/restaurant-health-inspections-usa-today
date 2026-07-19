"""New York State extractor — Socrata SODA API (the 'clean REST API' shape).

Pulls a bounded recent slice (inspections with `date` >= today - window_days), newest
first, up to sample_limit. Lands the raw SODA JSON array at
data/raw/new_york_state/inspections.json.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from ..http import fetch_json
from .base import ExtractResult, Extractor

EXPECTED = (
    "facility", "facility_address", "city", "zip_code", "date", "violations",
    "total_critical_violations", "total_crit_not_corrected", "total_noncritical_violations",
    "nys_health_operation_id", "county", "inspection_type", "food_service_facility_state",
)


class NewYorkStateExtractor(Extractor):
    EXPECTED_FIELDS = EXPECTED

    def extract(self) -> ExtractResult:
        soda = self.source.soda or {}
        base = soda["resource_url"]
        date_field = soda.get("date_field", "date")
        page_size = int(soda.get("page_size", 5000))
        cutoff = (datetime.now(timezone.utc) - timedelta(days=self.cfg.window_days)).date().isoformat()
        cap = self.cfg.sample_limit  # None => all in window

        where = quote(f"{date_field} >= '{cutoff}T00:00:00'")
        order = quote(f"{date_field} DESC")

        records: list[dict] = []
        offset = 0
        while True:
            limit = page_size if cap is None else min(page_size, cap - len(records))
            if limit <= 0:
                break
            url = f"{base}?$where={where}&$order={order}&$limit={limit}&$offset={offset}"
            page = fetch_json(url)
            if not page:
                break
            records.extend(page)
            offset += len(page)
            if len(page) < limit:
                break

        raw_path = self.raw_dir / "inspections.json"
        raw_path.write_text(json.dumps(records, indent=2) + "\n")

        present = sorted({k for r in records for k in r}) if records else []
        return ExtractResult(
            source=self.source.key,
            extracted_at=self.now_iso(),
            raw_paths=[raw_path],
            record_count=len(records),
            fields_present=present,
            missing_expected=self.check_fields(present),
            fingerprint=self.fingerprint(present),
            notes={"window_days": self.cfg.window_days, "cutoff": cutoff, "dataset_id": soda.get("dataset_id")},
        )
