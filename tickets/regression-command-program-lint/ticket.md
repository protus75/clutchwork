---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- none

## Runs before
- operator-deferral-snag

## Context
- clutch/tickets.py::lint_findings
- clutch/tickets.py::_regression
- clutch/stages.py::_base_worktree
- clutch/docs/host-authoring.md#The regression command
- tests/unit/test_ticket_lint_rules.py

## Goal / Why
On 2026-11-21 `serve-confirm-during-check` passed Implement, the full suite, lint and the head run of its reproducer, then failed Check because its `## Regression` command started with `.venv/bin/python`. Check runs that command a second time in a fresh base worktree (`_base_worktree`), which holds only committed files plus the carried ones and never a `.venv`, so the base run failed with `No such file or directory` and the run was thrown away. Lint accepted that command. After this ticket, lint refuses a `## Regression` command whose program is anything other than a bare program name looked up on PATH (such as `uv` or `python`) or a path under one of the ticket's `carries:` prefixes, so the mistake is caught before a run starts.

## Boundary contract
### Regression command program rule
- disposition: extend
- owner: clutch/tickets.py::lint_findings
- consumers: `clutch ticket lint`, `clutch ticket review` and every other authoring surface that calls `lint_findings`
- observable change: a new finding `` `## Regression` command runs <program>, which the base worktree does not have `` with paved road `start the command with a program on PATH, such as \`uv run python <carried reproducer>\`` when the command's first argument contains `/` and is not under a `carries:` prefix
- compatibility: commands starting with a bare name (`uv`, `python`) or a carried path stay valid; parsing (`parse_ticket`, `validate_ticket`, `_regression`) is unchanged, so settled and rejected tickets are not affected, as today
- acceptance: criteria 1 and 2
- tests: tests/unit/test_regression_command_program.py
- post-merge source of truth: clutch/tickets.py

## Scope in / Scope out
Scope in:
- clutch/tickets.py `lint_findings`: beside the existing "does not name a carried file" check, add the finding above when `ticket.regression[0]` contains `/` and no `ticket.carries` prefix equals it or is a directory prefix of it (the same path-matching rule that check already uses). `_regression` and parsing stay unchanged.
- clutch/docs/host-authoring.md section "The regression command": add one sentence saying the command runs again in a fresh base worktree with no `.venv`, so it starts with a program on PATH (such as `uv run python`) or a carried script, never `.venv/bin/...`. Refresh this file's `clutch:meta` block with `uv run clutch meta refresh clutch/docs/host-authoring.md` in the worktree.
- tests/unit/test_ticket_lint_rules.py `test_regression_requires_carried_path_not_runner_denylist` (lines 70-79): its fixture command `./dev.py test tests/x.py` now also gets the new finding, so update lines 75-76 to expect both findings, keeping the assertion that one says "does not name a carried file" with its existing paved road. Leave the shared `TEXT` fixture unchanged. Refresh this file's `clutch:meta` block with `uv run clutch meta refresh tests/unit/test_ticket_lint_rules.py`.
- New tests/unit/test_regression_command_program.py: build each ticket with `tickets.parse_ticket` against an in-memory repo, like the `repo` fixture in tests/unit/test_ticket_lint_rules.py, and call `tickets.lint_findings`. It reads no checkout files.
Scope out:
- `_regression` and ticket parsing, the base worktree setup in clutch/stages.py, the regression protocol, and existing ticket files.

## Scope fence
- clutch/tickets.py
- clutch/docs/host-authoring.md
- tests/unit/test_regression_command_program.py
- tests/unit/test_ticket_lint_rules.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_regression_command_program.py` proves `.venv/bin/python tests/regress_x.py` with `- carries: tests/regress_x.py` gets the new finding, and `venv/bin/python tests/regress_x.py` gets it too (any unlisted relative path, not only `.venv`).
2. `./dev.py test tests/unit/test_regression_command_program.py` proves `uv run python tests/regress_x.py`, `python tests/regress_x.py` and `tests/regress_x.py` (carried) get no new finding.
3. `uv run clutch ticket lint` reports no new finding for any current non-settled ticket (a one-time review check run in the worktree).
4. `./dev.py test tests/unit/test_ticket_lint_rules.py` passes with the updated expectation for the `./dev.py test tests/x.py` fixture.

## Verification
```
./dev.py test tests/unit/test_regression_command_program.py tests/unit/test_ticket_lint_rules.py
uv run clutch meta check clutch/docs/host-authoring.md
uv run clutch meta check tests/unit/test_ticket_lint_rules.py
```

## Definition of rejected
A denylist that refuses only `.venv`, putting the rule in `_regression` or another parse-time path, a change to how Check runs the base, or files outside the fence change.

## Time budget
- expected: 8m
- stuck: 16m