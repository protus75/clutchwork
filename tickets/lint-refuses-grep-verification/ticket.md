---
state: confirmed
source: box:suggestion
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/tickets.py::lint_findings
- clutch/docs/host-authoring.md#What each section is for
- tests/unit/test_ticket_lint_rules.py::TEXT
- tests/unit/test_regression_command_program.py
- tests/integration/test_lint_guide_parity.py

## Goal / Why
Check requires every Verification command to exit 0, but `rg` and `grep` exit 1 when they find no match. A ticket that uses one as an absence check (print nothing, so the pattern is gone) can never pass once the work is correct. The owner reports `llm-request-subject` lost two attempts with a correct diff for this reason, and lint passes the form today because nothing in `clutch/tickets.py` checks the Verification program. The host policy uses a consistent rule for direct search commands because their argv does not express whether a match counts as success. The paved road is an explicit assertion in a ticket-owned test or check command. Siblings: `lint-refuses-two-dot-git-diff-main` covers a different broken command form, and declined-box-000435 asked only for authoring prose and did not cover the exit-code trap.

## Boundary contract
### Ticket lint rules
- disposition: extend
- owner: clutch/tickets.py (`lint_findings`)
- consumers: `clutch ticket lint`, intake, and the author/review stages that call `lint_findings`
- observable change: one new finding when any `## Verification` argv starts with `rg`, `grep`, `egrep`, `fgrep` or `ripgrep` (matched on the program's basename). The finding directs the author to put the intended positive or negative assertion in a ticket-owned test or check command.
- compatibility: tickets whose Verification programs are other programs, including `uv run`, `./dev.py test` and `python`, lint exactly as before. Existing merged and rejected tickets are not re-linted by this change.
- acceptance: a ticket whose Verification starts with `rg` or `grep` yields exactly one finding, and a ticket using `./dev.py test` yields none
- tests: new `tests/unit/test_ticket_lint_verification_search.py`
- post-merge source of truth: clutch/tickets.py and the authoring guide `clutch/docs/host-authoring.md`

## Scope in / Scope out
In: in `lint_findings`, add one finding per `ticket.verification` command whose first argument's basename is `rg`, `grep`, `egrep`, `fgrep` or `ripgrep`. In `clutch/docs/host-authoring.md`, add one sentence to the `Verification` bullet of "What each section is for": a search program such as `rg` or `grep` exits 1 on no match, so use direct searches for acceptance-criterion inspection. Verification refuses standalone search commands, including positive searches. Put positive and negative assertions in a ticket-owned test or check command with a pass/fail exit code instead. Add the new unit test file and extend the integration guide parity test to require the direct-search rule.
Out: no new command group or verb. No linting of programs other than the search family, and no parsing of shell pipelines or `uv run rg` wrappers. No edits to other lint rules, `docs/how-clutch-works.md` or any prompt spec. Any `meta` header refresh for the touched guide is handled by Check's meta step.

## Scope fence
- clutch/tickets.py
- clutch/docs/host-authoring.md
- tests/unit/test_ticket_lint_verification_search.py
- tests/integration/test_lint_guide_parity.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_ticket_lint_verification_search.py` passes. For each program in `rg`, `grep`, `egrep`, `fgrep` and `ripgrep`, `lint_findings` on a ticket whose Verification command is that program followed by a pattern and a path returns exactly one finding that names the program and a paved road mentioning the unit test. It does not return an empty list.
2. In the same test file, a Verification of `./dev.py test tests/x.py` and one of `uv run python tests/regress_x.py` each return `[]`, not a finding, so the rule does not flag non-search programs.
3. In the same test file, a path-qualified program `/usr/bin/grep -r x .` is flagged, matching on basename. A program such as `rgx` is not flagged, so the match is exact and not a prefix.
4. `./dev.py test tests/unit/test_ticket_lint_rules.py tests/unit/test_regression_command_program.py tests/integration/test_lint_guide_parity.py` passes, and the extended parity check fails if the authoring guide omits the direct-search rule.

## Verification
```
./dev.py test tests/unit/test_ticket_lint_verification_search.py tests/unit/test_ticket_lint_rules.py tests/unit/test_regression_command_program.py tests/integration/test_lint_guide_parity.py
```

## Definition of rejected
A branch is rejected if the rule flags any non-search Verification program, if it uses a prefix match so that `rgx` is flagged, if the finding has no paved road, or if the rule is added without the guide sentence.

## Time budget
- expected: 15m
- stuck: 30m
