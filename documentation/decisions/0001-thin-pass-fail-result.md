# 0001 — Thin pass/fail with fixed per-source rules

**Status:** Accepted (2026-07-18)

## Context
The three regulators express "how did the inspection go?" completely differently. NY publishes
violation *counts* (critical / critical-not-corrected / non-critical), LA publishes a 0–100 *score*
and an A/B/C *grade*, and ABQ publishes a *status* string (Approved / Conditional Approved /
Unsatisfactory / Closure) plus an operational Open/Closed flag. There is no shared native outcome.
The initial data model proposed a binary pass/fail, but with rules that were partly wrong (it would
have marked an ABQ "Unsatisfactory Re-Inspection required" as a *pass*).

## Decision
Emit a thin binary `inspection_result` of `pass`, `fail`, or `unknown`, derived per source, and always
record a plain-language `result_basis` so a reporter can see why:

- **NY**: `fail` if `total_crit_not_corrected > 0`, else `pass`. An uncorrected critical violation is
  the meaningful risk signal; a critical that was corrected on site is not a failure.
- **LA**: `fail` if `SCORE < 70`, else `pass`; `unknown` if there's no score. The native `score` and
  `grade` are carried through unchanged for anyone who wants them.
- **ABQ**: `fail` if the status contains *unsatisfactory* or *closure*, or the operational status is
  *Closed*; else `pass`. This corrects the draft rule.

`unknown` is explicit: a record we can't classify is never silently called `pass`.

## Consequences
- A comparable one-field signal across sources for alerts and tip-sheets, with `result_basis` for
  trust.
- It is a flattening. The `score`, `grade`, and violation counts stay in the record for nuance.
- Deferred, and the main thing a fuller build would add: the per-source rules here are ad hoc, one
  function per transformer. With many more sources they should become a **shared, versioned catalog
  of `result_rules`** (each rule named, documented, and referenced by id from the record) instead of
  bespoke logic per source. On top of that, a normalized 0–100 **risk index** across sources (the
  assignment's "issues to incorporate") would give a single comparable severity measure. The schema
  leaves room for both; neither is built in this PoC. Supersede this ADR when they land.
