"""City of Albuquerque extractor — the weekly 'Media Report' PDF (the 'scrape' shape).

The PDF is a rolling latest-week report. We parse the SUMMARY TABLE only (ADR 0004):
per establishment, a header line `NAME - ADDRESS`, one or more permit lines carrying the
permit # and operational status, and one or more inspection rows
`DATE  INSPECTION_ID  TYPE  STATUS  Pg. N`.

Text is extracted with the system `pdftotext -layout` (poppler) — no Python PDF
dependency. Raw artifacts kept for provenance: the .pdf, the .txt, and the structured
summary.json the transform reads.
"""

from __future__ import annotations

import json
import re
import subprocess

from ..http import fetch_bytes
from .base import ExtractResult, Extractor

# A summary inspection row: DATE  ID  TYPE  STATUS  Pg. N  (columns are 2+ spaces apart).
_ROW = re.compile(
    r"^\s*(\d{1,2}/\d{1,2}/\d{4})\s+(\S.*?)\s{2,}(\S.*?)\s{2,}(\S.*?)\s{2,}Pg\.?\s*(\d+)\s*$"
)
# Permit + operational status line (dash may be hyphen or en-dash).
_PERMIT = re.compile(
    r"\(Permit\s*#\s*[-–]\s*(.+?)\)\s*[-–]\s*Operational Status\s*[-–]\s*(\w+)", re.IGNORECASE
)
_HEADER = re.compile(r"^Inspection Date\s+Inspection ID", re.IGNORECASE)
_FOOTER = re.compile(r"^\s*Page\s+\d+\s+of\s+\d+\s*$", re.IGNORECASE)

EXPECTED_COLUMNS = ("Inspection Date", "Inspection ID Number", "Inspection Type", "Inspection Status")


def pdf_to_text(pdf_path) -> str:
    proc = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        capture_output=True, text=True, check=True,
    )
    return proc.stdout


def _dedupe_address(addr: str) -> str:
    """ABQ headers sometimes repeat the address ('5604 X NE 5604 X NE'). Collapse it."""
    toks = addr.split()
    n = len(toks)
    if n and n % 2 == 0 and toks[: n // 2] == toks[n // 2:]:
        toks = toks[: n // 2]
    return " ".join(toks)


def parse_summary(text: str) -> list[dict]:
    """Walk the layout text and emit one dict per summary inspection row."""
    rows: list[dict] = []
    last_content = ""          # most recent content line (the NAME - ADDRESS header lands here)
    establishment = address = permit = op_status = ""

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or _FOOTER.match(line):
            continue

        if _HEADER.match(line.strip()):
            # The establishment header is the content line immediately above this.
            name, _, addr = last_content.partition(" - ")
            establishment = name.strip()
            address = _dedupe_address(addr.strip())
            permit = op_status = ""
            continue

        pm = _PERMIT.search(line)
        if pm:
            permit, op_status = pm.group(1).strip(), pm.group(2).strip()
            # fall through: a permit line is never also a data row

        rm = _ROW.match(line)
        if rm and not _PERMIT.search(line):
            date, insp_id, insp_type, status, page = (g.strip() for g in rm.groups())
            rows.append({
                "establishment_name": establishment,
                "address": address,
                "permit": permit,
                "operational_status": op_status,
                "inspection_date": date,
                "inspection_id": insp_id,
                "inspection_type": insp_type,
                "inspection_status": status,
                "page": page,
            })
            continue

        if not pm:
            last_content = line.strip()

    return rows


class AlbuquerqueCityExtractor(Extractor):
    EXPECTED_FIELDS = EXPECTED_COLUMNS

    def extract(self) -> ExtractResult:
        pdf_cfg = self.source.pdf or {}
        pdf_path = self.raw_dir / "media_report.pdf"
        pdf_path.write_bytes(fetch_bytes(pdf_cfg["report_url"]))

        text = pdf_to_text(pdf_path)
        (self.raw_dir / "media_report.txt").write_text(text)

        rows = parse_summary(text)
        # Report-week banner, e.g. "Week: July 05, 2026 to July 11, 2026".
        week = ""
        m = re.search(r"Week:\s*(.+?)\s*$", text, re.MULTILINE)
        if m:
            week = m.group(1).strip()

        summary_path = self.raw_dir / "summary.json"
        summary_path.write_text(json.dumps(rows, indent=2) + "\n")

        # Drift check: confirm the expected column header line still appears.
        header_present = bool(re.search(r"Inspection Date\s+Inspection ID Number", text))
        missing = [] if header_present else list(EXPECTED_COLUMNS)

        return ExtractResult(
            source=self.source.key,
            extracted_at=self.now_iso(),
            raw_paths=[pdf_path, self.raw_dir / "media_report.txt", summary_path],
            record_count=len(rows),
            fields_present=list(EXPECTED_COLUMNS) if header_present else [],
            missing_expected=missing,
            fingerprint=self.fingerprint(list(EXPECTED_COLUMNS)),
            notes={"report_week": week, "scope": pdf_cfg.get("scope", "summary_table")},
        )
