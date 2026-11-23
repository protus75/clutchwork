---
state: confirmed
source: box:suggestion
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Runs before
- lint-refuses-grep-verification

## Context
- clutch/tickets.py::lint_findings
- clutch/tickets.py::_criteria
- tests/unit/test_ticket_lint_rules.py
- tests/integration/test_lint_guide_parity.py

## On-demand
- clutch/docs/host-authoring.md

## Goal / Why
A criterion or `## Verification` command that runs `git diff --name-only main` (two dots, or a bare `main`) compares the worktree to main as it is now. When another ticket merges after the attempt's base commit, the diff lists that ticket's files and an in-fence-only criterion fails. `visual-baseline-fixtures` attempt 0 ended premise_failed on this (2026-11-19). The `docs-truth-after-040` run record shows the same false difference. The form appears in `boundary-contract-trial`, `docs-truth-after-040`, `engine-state-duckdb-plan`, `shared-serve-rig-config`, `requisition-review-bare-json-pin` and, before its fix, `visual-baseline-fixtures`. All of those are merged or rejected, so no live ticket needs editing.

After this change `clutch ticket lint` refuses the form with the paved road `git diff --name-only main...HEAD`, which compares against the merge base. The host authoring guide states the rule.

## Boundary contract
### Ticket lint rules
- disposition: extend
- owner: clutch/tickets.py (`lint_findings`)
- consumers: `clutch ticket lint`, intake, `clutch ticket review`, the Author stage
- observable change: a ticket whose `## Acceptance criteria` or `## Verification` contains `git diff` with `--name-only` and a `main` ref not followed by `...` gets one finding naming the section and the road `main...HEAD`
- compatibility: tickets without the two-dot form lint exactly as before; settled and rejected tickets stay exempt as for other lint rules
- acceptance: unit tests lint a two-dot ticket (finding, names the section) and a `main...HEAD` ticket (no such finding)
- tests: tests/unit/test_ticket_lint_git_diff_base.py
- post-merge source of truth: clutch/tickets.py

### Host authoring guide
- disposition: extend
- owner: clutch/docs/host-authoring.md
- consumers: ticket authors, the Author stage prompt
- observable change: the Acceptance criteria and Verification guidance states that a diff against main uses `main...HEAD`
- compatibility: other guide text unchanged
- acceptance: the guide parity test finds the stated phrase
- tests: tests/integration/test_lint_guide_parity.py
- post-merge source of truth: clutch/docs/host-authoring.md

## Scope in / Scope out
In: in `lint_findings` in clutch/tickets.py, add one check over the `Acceptance criteria` text and the joined `ticket.verification` argv. It matches `git diff` followed on the same line by `--name-only` and a `main` ref not followed by `...`. This covers `main`, `main..HEAD` and `main HEAD`. The finding road is "compare with the merge base: `git diff --name-only main...HEAD`". In clutch/docs/host-authoring.md, add one sentence to the `Acceptance criteria` bullet saying a changed-files check uses `main...HEAD`, never `main`. In tests/integration/test_lint_guide_parity.py, add that phrase to the tuple of required phrases. Add the new unit test file.
Out: editing any existing ticket, other lint rules, other `git diff` forms (`--stat`, no `--name-only`).

## Scope fence
- clutch/tickets.py
- clutch/docs/host-authoring.md
- tests/unit/test_ticket_lint_git_diff_base.py
- tests/integration/test_lint_guide_parity.py

## Acceptance criteria
1. A ticket with a criterion containing `git diff --name-only main` yields one lint finding naming `## Acceptance criteria` and `main...HEAD`; `./dev.py test tests/unit/test_ticket_lint_git_diff_base.py` rules out the finding list being empty.
2. A `## Verification` command `git diff --name-only main..HEAD` yields a finding naming `## Verification`; the test rules out it passing silently.
3. A criterion or command using `git diff --name-only main...HEAD` yields no such finding; `./dev.py test tests/unit/test_ticket_lint_git_diff_base.py` rules out a false positive on the merge-base form.
4. The guide states the `main...HEAD` rule; `./dev.py test tests/integration/test_lint_guide_parity.py` passes.

## Verification
```
./dev.py test tests/unit/test_ticket_lint_git_diff_base.py tests/unit/test_ticket_lint_rules.py tests/integration/test_lint_guide_parity.py
```

## Definition of rejected
The lint refuses the `main...HEAD` form, or lets the two-dot form pass, or the change edits any existing ticket.

## Time budget
- expected: 20m
- stuck: 40m
