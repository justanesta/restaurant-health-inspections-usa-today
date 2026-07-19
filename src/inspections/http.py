"""Tiny stdlib HTTP helper with transient-vs-permanent error handling.

Lowest-footprint by design (no requests/httpx). Distinguishes:
  * transient (5xx, 408, 429, connection/timeout)  -> retried with linear backoff
  * permanent (other 4xx)                           -> raised immediately, no retry
This is the retry/alert boundary the project's error-handling standard asks for.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

_UA = "usatoday-inspections-poc/0.1 (+https://usatoday.example)"
_TRANSIENT_STATUS = {408, 429, 500, 502, 503, 504}


class TransientHTTPError(Exception):
    """Retryable failure — exhausted after N attempts."""


class PermanentHTTPError(Exception):
    """Non-retryable failure (e.g. 404) — surfaces at once."""


def fetch_bytes(
    url: str,
    *,
    timeout: float = 90.0,
    retries: int = 3,
    backoff: float = 2.0,
    headers: dict[str, str] | None = None,
) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": _UA, **(headers or {})})
    last: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code not in _TRANSIENT_STATUS:
                raise PermanentHTTPError(f"{exc.code} {exc.reason} for {url}") from exc
            last = exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last = exc
        if attempt < retries:
            time.sleep(backoff * attempt)
    raise TransientHTTPError(f"failed after {retries} attempts: {url} ({last})")


def fetch_json(url: str, **kw: Any) -> Any:
    return json.loads(fetch_bytes(url, **kw))


def fetch_text(url: str, **kw: Any) -> str:
    return fetch_bytes(url, **kw).decode("utf-8", errors="replace")
