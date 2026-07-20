# 0004 — Albuquerque: parse the summary table only

**Status:** Accepted (2026-07-18)

## Context
The ABQ weekly "Media Report" PDF has two layers: a clean **summary table** (pp. 1–4: establishment,
permit, operational status, and per-inspection date / id / type / status) and **detail pages**
(pp. 5–37) with per-violation narrative in free text. The summary is reliably machine-parseable with
`pdftotext -layout`; the detail pages are messy prose.

## Decision
Parse the **summary table only**. `violations` is `[]` for ABQ, and the outcome comes from the status
field ([0001](0001-thin-pass-fail-result.md)). Detail-page violation extraction is explicitly
**future work**.

## Consequences
- ABQ contributes establishment, result, and type reliably, with no violation detail: a low-fragility
  slice. `total_violation_count` is null (unknown), not zero (which would imply clean).
- The summary parser already handles the real edge cases (verified against a live report): multiple
  permits per establishment, multiple inspections per establishment, en-dash vs hyphen, repeated
  addresses, page footers.
- Adding detail-page violations later is additive (populate `violations`); it changes no other field
  and needs no schema change.
