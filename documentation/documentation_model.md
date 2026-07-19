# Documentation Model (PoC edition)

**Status:** Active · **Audience:** future maintainers · **Purpose:** say where each kind of
fact lives so docs don't rot. Pared down from the
[full operating model](https://github.com/justanesta/consumer-product-recalls/blob/main/documentation/documentation_model.md).

## The one rule

**Every fact has exactly one home. Other docs *point* at that home** (by anchor, never by
line number). If you're tempted to restate something, link instead.

## Document types used in this repo

| Type | Answers | Home | Lifecycle |
|---|---|---|---|
| **README** | What is this, how do I run it | `README.md` | living |
| **ADR** | *Why* a decision was made | `documentation/decisions/NNNN-*.md` | Accepted → Superseded |
| **Reference** | *What* the system is (architecture, schema, dev, ops) | `documentation/*.md` | living |
| **Findings** | *What we observed* about a source (probe results, as-built) | `documentation/sources/*_findings.md` | append-only, dated |
| **Scope** | The assignment + author intent | `project_scope/`, `data_sources/` | frozen inputs |
| **Answer sheet** | The assignment deliverable | `documentation/answer_sheet.md` | living |

There is no separate master-plan / phase-plan / branch-sequencing tier here — this is a
single-slice PoC, so that machinery would be overhead. The task list lives in the tool, not a file.

## Where does new information go? (decision tree)

- It's *why we chose X* → **ADR**. Give it the next number; reference it from the code.
- It's *how the system is built* (stable) → the matching **reference** doc.
- It's *what a source actually looks like* (could change upstream) → a **findings** doc, dated.
- It's *how to run/operate it* → **development.md** / **operations.md**.
- It's a loose end → the task list.

## Conventions

- **Status line first** on ADRs and long-lived docs.
- **Anchors, not line numbers**, for cross-references (line numbers rot).
- **Dated, append-only** findings — never rewrite history, add a new dated section.
- Keep it thin. If a doc is mostly restating code or another doc, delete and link.
