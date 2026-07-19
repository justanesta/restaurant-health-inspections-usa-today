"""Minimal structured (JSON) logging.

One event per line to stderr: {"ts","level","event", ...fields}. Lowest-footprint way
to satisfy the project's structured-logging requirement; a real deployment would swap
this for structlog + a shipper (CloudWatch/Datadog) without changing call sites.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone


def event(name: str, level: str = "info", **fields) -> None:
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "event": name,
        **fields,
    }
    print(json.dumps(record, default=str), file=sys.stderr)
