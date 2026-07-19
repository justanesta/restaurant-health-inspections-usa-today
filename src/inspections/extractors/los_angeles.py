"""Los Angeles County extractor — two ArcGIS Hub CSV flat files (the 'multi-file' shape).

Downloads the full inspections + violations CSVs, filters inspections to a bounded
recent window by ACTIVITY DATE (newest first, capped at sample_limit), then keeps only
the violation rows whose SERIAL NUMBER survives the filter. Lands the (small) filtered
slices at data/raw/los_angeles_county/{inspections,violations}.csv.

In production we'd push the date filter server-side via the ArcGIS Feature Service query
API (`where=ACTIVITY_DATE > ...`) instead of downloading the whole file; the /data CSV
item is used here because the source notes point at it and it keeps the PoC dependency-free.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone

from ..http import fetch_bytes
from .base import ExtractResult, Extractor

INSPECTION_EXPECTED = (
    "ACTIVITY DATE", "FACILITY NAME", "FACILITY ADDRESS", "FACILITY CITY",
    "FACILITY STATE", "FACILITY ZIP", "SCORE", "GRADE", "SERIAL NUMBER",
    "FACILITY ID", "SERVICE DESCRIPTION",
)
VIOLATION_EXPECTED = ("SERIAL NUMBER", "VIOLATION CODE", "VIOLATION DESCRIPTION", "VIOLATION STATUS", "POINTS")


def _parse_date(value: str):
    return datetime.strptime(value.strip(), "%m/%d/%Y").date()


def _decode(blob: bytes) -> str:
    """LA's export mixes UTF-8 with stray CP1252 bytes (e.g. smart quotes). Degrade safely."""
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return blob.decode(enc)
        except UnicodeDecodeError:
            continue
    return blob.decode("latin-1")


def _read_csv(blob: bytes) -> tuple[list[str], list[dict]]:
    reader = csv.DictReader(io.StringIO(_decode(blob)), skipinitialspace=True)
    rows = [{(k or "").strip(): (v or "").strip() for k, v in row.items()} for row in reader]
    fields = [f.strip() for f in (reader.fieldnames or [])]
    return (fields, rows)


class LosAngelesCountyExtractor(Extractor):
    EXPECTED_FIELDS = INSPECTION_EXPECTED

    def extract(self) -> ExtractResult:
        ag = self.source.arcgis or {}
        date_field = ag.get("date_field", "ACTIVITY DATE")
        join_key = ag.get("join_key", "SERIAL NUMBER")
        cutoff = (datetime.now(timezone.utc) - timedelta(days=self.cfg.window_days)).date()
        cap = self.cfg.sample_limit

        insp_fields, inspections = _read_csv(fetch_bytes(ag["inspections_url"]))
        vio_fields, violations = _read_csv(fetch_bytes(ag["violations_url"]))

        # Filter to the recent window, newest first, then cap.
        windowed = []
        for row in inspections:
            raw_date = row.get(date_field, "")
            try:
                if _parse_date(raw_date) >= cutoff:
                    windowed.append(row)
            except ValueError:
                continue  # unparseable date -> excluded from the slice (extractor stays lenient)
        windowed.sort(key=lambda r: _parse_date(r[date_field]), reverse=True)
        if cap is not None:
            windowed = windowed[:cap]

        keep_serials = {r[join_key] for r in windowed}
        kept_violations = [v for v in violations if v.get(join_key) in keep_serials]

        insp_path = self.raw_dir / "inspections.csv"
        vio_path = self.raw_dir / "violations.csv"
        _write_csv(insp_path, insp_fields, windowed)
        _write_csv(vio_path, vio_fields, kept_violations)

        missing = self.check_fields(insp_fields) + [
            f"violations::{m}" for m in _missing(vio_fields, VIOLATION_EXPECTED)
        ]
        return ExtractResult(
            source=self.source.key,
            extracted_at=self.now_iso(),
            raw_paths=[insp_path, vio_path],
            record_count=len(windowed),
            fields_present=insp_fields,
            missing_expected=missing,
            fingerprint=self.fingerprint(insp_fields + vio_fields),
            notes={
                "window_days": self.cfg.window_days,
                "cutoff": cutoff.isoformat(),
                "violation_rows": len(kept_violations),
            },
        )


def _missing(present, expected) -> list[str]:
    have = set(present)
    return [f for f in expected if f not in have]


def _write_csv(path, fieldnames, rows) -> None:
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
