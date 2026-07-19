"""Loud, findable data-quality error handling.

Requirement: schema/integrity errors must be handled, LOUD, and easy to find in the
repo — never silently skipped. Bad records are collected in an ErrorSink and flushed to
a timestamped plain-text file under data/errors/, with a banner printed to stderr. The
pipeline continues (dead-letter style) so one bad record can't sink a whole run, but the
run's exit status reflects that errors occurred.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import paths


@dataclass
class QualityError:
    identifier: str
    reason: str
    detail: str | None = None


class ErrorSink:
    """Collects data-quality errors for one (stage, source) and flushes them loudly."""

    def __init__(self, stage: str, source: str):
        self.stage = stage
        self.source = source
        self.errors: list[QualityError] = []

    def record(self, identifier: object, reason: str, detail: str | None = None) -> None:
        self.errors.append(QualityError(str(identifier), reason, detail))

    @property
    def count(self) -> int:
        return len(self.errors)

    def __bool__(self) -> bool:
        return bool(self.errors)

    def flush(self) -> Path | None:
        """Write a plain-text report if there are errors. Returns the path or None."""
        if not self.errors:
            return None
        paths.ensure_data_dirs()
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = paths.ERRORS_DIR / f"{self.stage}__{self.source}__{ts}.txt"

        lines = [
            "!!! DATA QUALITY ERRORS !!!",
            f"stage      : {self.stage}",
            f"source     : {self.source}",
            f"generated  : {datetime.now(timezone.utc).isoformat()}",
            f"error_count: {self.count}",
            "-" * 72,
        ]
        for i, e in enumerate(self.errors, 1):
            lines.append(f"[{i}] id={e.identifier} | {e.reason}")
            if e.detail:
                for dl in e.detail.splitlines():
                    lines.append(f"      {dl}")
        path.write_text("\n".join(lines) + "\n")

        print(
            f"\n⚠️  {self.count} DATA QUALITY ERROR(S) in {self.stage}/{self.source} "
            f"-> {path}\n",
            file=sys.stderr,
        )
        return path
