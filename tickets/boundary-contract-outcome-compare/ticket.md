---
state: draft
source: human
priority: P1
kind: chore
---

## Depends on
- boundary-contract-implementation-review

## Context
- docs/boundary-contract-plan.md#Rollout
- docs/boundary-contract-plan.md#Trial results
- docs/boundary-contract-plan.md#Measures of success
- docs/boundary-contract-plan.md#Status
- clutch/docs/host-running.md

## Goal / Why
Phase 3 of `docs/boundary-contract-plan.md` says to measure premise failures, review findings, rework and duplicate-owner incidents before and after the change, and roadmap row 153 says to compare them with the trial baseline. Row 153 merged at commit `adf7d00b` (committed 2026-11-20T00:08:40-05:00, 05:08:40 UTC). The plan records only the paper trial baseline (its `### Baseline findings` lists historical risks and gives no counts), so the comparison does not exist anywhere. After this ticket the plan has a `### Outcome comparison` subsection under `## Trial results`, placed after `### Baseline findings`, that records the measured numbers, or says a quantity is not measurable and why. Why: the owner decides on stronger lint (row 152) from these outcomes, and they are read from the journal now, not recalled later.

## Boundary contract
none
- reason: documentation corrections without behavior change; the edit adds a measurement record to one plan document and no producer, consumer, parser, output, failure or format of any code changes.

## Scope in / Scope out
Scope in. Add `### Outcome comparison` to `docs/boundary-contract-plan.md` after `### Baseline findings` and before `## Measures of success`. Measure with these existing verbs only and never hand-build their argv or read the journal file directly:
- `clutch view stats --window <N>h --json`, where N is the whole number of hours from 2026-11-20T05:08:40Z to now, rounded down so the printed `window.start` is after the merge. This is the after window. Its fields: `failures.terminals` keys `premise_failed@implement` and `premise_failed@requisition` (premise failures), `failures.rework` (rework: `update`, `split`, `escalate` counts), `cycles.all.review_snags_mean` and `cycles.all.first_pass_yield` (review findings), and `throughput.settled.merged` (the denominator).
- The same verb with `--window <N+168>h`. The stats window only trails from now and has no end bound, so the before figures are the count fields of this longer window minus the same fields of the after window, covering the 168 hours before the merge. Report means and yields for the before period as not measurable (a mean cannot be subtracted), and give counts both raw and per merged ticket using `throughput.settled.merged` of each period.
- `clutch view stats` is read-only and needs no lock. If it cannot read the journal from the ticket worktree, report every quantity as not measurable with that reason; never copy numbers from memory or another source.

Duplicate-owner findings: no verb counts them. Review findings use only the existing `acceptance` and `scope` codes (row 153 added no code), so a duplicate-owner finding is not separable in `clutch view stats` output. Report this quantity as not measurable by an existing verb, state that reason in the subsection, and give no number. Do not add a finding code, a verb or a stats field.

The subsection states: the merge commit and time above, the two window specs used and each printed `window.start` and `window.end`, a table of before and after values for each measurable quantity, the figures marked not measurable with their reason, and one sentence reading the result against the plan's `## Measures of success` list without claiming causation from two windows. The before figures come from tickets that predate row 153 and the plan's trial baseline has no counts, so say that the trial baseline is qualitative and the before window is the quantitative reference.

Also edit `## Status`: in its sentence naming open roadmap rows, drop row 208 from the open list and name row 208 (`boundary-contract-outcome-compare`) as merged only if the same sentence already lists merged rows that way; otherwise leave the sentence unchanged apart from the open list. After the edit run `clutch meta refresh docs/boundary-contract-plan.md`; it may change only that file's metadata header (`verified` and `hash`), never other header fields.

Scope out: no code, tests, other documents, roadmap edits or changes to `clutch/specs/`. No standing test or criterion pinning the plan's text. Row 152 stays open and is not touched.

## Scope fence
- docs/boundary-contract-plan.md

## Acceptance criteria
1. `docs/boundary-contract-plan.md` contains a `### Outcome comparison` subsection placed after `### Baseline findings` and before `## Measures of success`, checked by reading it after `uv run clutch meta check docs/boundary-contract-plan.md` exits 0.
2. Every number in the subsection is one printed by `clutch view stats --json` for the two windows the subsection names, or a difference of two printed counts; a quantity the verb cannot give (duplicate-owner findings, and before-period means) is stated as not measurable with its reason, not as a number or zero, checked by re-running the two named `clutch view stats` commands and comparing.
3. The header of `docs/boundary-contract-plan.md` differs from `git show HEAD:docs/boundary-contract-plan.md` only in `verified` and `hash`, checked with `git diff HEAD -- docs/boundary-contract-plan.md`.
4. `git diff HEAD --stat` lists only `docs/boundary-contract-plan.md`.

## Verification
```
uv run clutch meta check docs/boundary-contract-plan.md
```

## Definition of rejected
The subsection contains a number not produced by the named verbs, reports duplicate-owner findings as a number, edits any file but `docs/boundary-contract-plan.md`, changes the plan header beyond `verified` and `hash`, or adds a test pinning plan text.

## Time budget
- expected: 20m
- stuck: 40m
