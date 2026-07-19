# 0001 — Thin pass/fail with fixed per-source rules

**Status:** Accepted (2026-07-18)

## Context
The three regulators express "how did the inspection go?" completely differently: NY publishes
violation *counts* (critical / critical-not-corrected / non-critical), LA publishes a 0–100
*score* and an A/B/C *grade*, ABQ publishes a *status* string (Approved / Conditional Approved /
Unsatisfactory / Closure) plus an operational Open/Closed flag. There is no shared native outcome.
The initial data model proposed a binary pass/fail but with rules that were partly wrong (it would
have marked an ABQ "Unsatisfactory Re-Inspection required" as a *pass*).

## Decision
Emit a **thin binary** `inspection_result` ∈ {pass, fail, unknown}, derived per source, and always
record a plain-language `result_basis` so a reporter can see *why*:

- **NY** — `fail` if `total_crit_not_corrected > 0`, else `pass`. (Uncorrected critical violation is
  the meaningful risk signal; a corrected-on-site critical is not a "failure".)
- **LA** — `fail` if `SCORE < 70`, else `pass`. `unknown` if no score. Native `score`/`grade` are
  carried through unchanged for anyone who wants them.
- **ABQ** — `fail` if the status contains *unsatisfactory* / *closure* or operational status is
  *Closed*; else `pass`. This corrects the draft rule.

`unknown` is explicit — a record we can't classify is never silently called `pass`.

## Consequences
- Comparable one-field signal across sources for alerts/tip-sheets, with `result_basis` for trust.
- It is a **flattening**. `score`/`grade`/violation counts remain in the record for nuance.
- Deferred (see the assignment's "issues to incorporate"): a normalized 0–100 **risk index** across
  sources. The schema leaves room for it; it is not built in this PoC. Supersede this ADR when it is.
