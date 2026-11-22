---
state: draft
source: human
priority: P0
kind: feature
---

## Depends on
- shared-git-fake-unit-4

## Context
- clutch/git.py::Git

## Goal / Why
`shared-git-fake` created `tests/git_fake.py::GitFake` and `tests/integration/test_git_fake_adoption.py`, whose `PENDING` list names the files still holding a hand-built `Git` stand-in. This ticket migrates 13 of them (18 stand-ins) onto `GitFake` and removes them from `PENDING`, so those tests no longer break when `Git` gains a method. Read `tests/git_fake.py` in the worktree for the override and `calls` contract before editing; it is a merged dependency.

## Boundary contract
none
- reason: tests encoding an existing contract; the stand-ins move to the existing `tests/git_fake.py::GitFake` with the same assertions and no production, document or behavior change

## Scope in / Scope out
In: migrate each stand-in in the files below onto `GitFake` from `tests/git_fake.py`, keeping every existing assertion and test name (an `assert_awaited_with` on a stand-in becomes an assertion on `fake.calls`). Add only the import `GitFake` needs and nothing else changes in a file. Remove each migrated file from `PENDING` in `tests/integration/test_git_fake_adoption.py`; that is the only edit allowed there. A test using a real `Git` on a fake process executor is not a stand-in and stays as is.

Files migrated here (stand-ins counted):
tests/unit/test_runner_attempt_manifest.py (2)
tests/unit/test_runner_terminal_removal_shield.py (1)
tests/unit/test_serve_idle_poll.py (1)
tests/unit/test_spool_store_switch.py (1)
tests/unit/test_stages_candidates_select.py (1)
tests/unit/test_stages_conflict_rerun_inputs.py (1)
tests/unit/test_stages_flake_coverage.py (1)
tests/unit/test_stale_running.py (4)
tests/unit/test_supervise_idle_point.py (1)
tests/unit/test_supervisor_trigger.py (1)
tests/unit/test_ticket_lint_rules.py (1)
tests/unit/test_ticket_write_consumers_author.py (1)
tests/unit/test_ticket_write_consumers_runner.py (2)

Out: production code under `clutch/`; `tests/git_fake.py` (when a stand-in needs a capability `GitFake` lacks, give the fake the capability through an override callable in the test, and name the gap in the run record); `tests/fakes.py`; the five `tests/regress_*.py` files; every file not listed above.

## Scope fence
- tests/integration/test_git_fake_adoption.py
- tests/unit/test_runner_attempt_manifest.py
- tests/unit/test_runner_terminal_removal_shield.py
- tests/unit/test_serve_idle_poll.py
- tests/unit/test_spool_store_switch.py
- tests/unit/test_stages_candidates_select.py
- tests/unit/test_stages_conflict_rerun_inputs.py
- tests/unit/test_stages_flake_coverage.py
- tests/unit/test_stale_running.py
- tests/unit/test_supervise_idle_point.py
- tests/unit/test_supervisor_trigger.py
- tests/unit/test_ticket_lint_rules.py
- tests/unit/test_ticket_write_consumers_author.py
- tests/unit/test_ticket_write_consumers_runner.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_git_fake_adoption.py` passes: the 13 files named in Scope in have zero matches for the three patterns and are absent from `PENDING`, and the test fails (not passes) when a `PENDING` entry has no remaining match or an unlisted file contains `git = SimpleNamespace(`.
2. `./dev.py test tests/unit/test_runner_attempt_manifest.py tests/unit/test_runner_terminal_removal_shield.py tests/unit/test_serve_idle_poll.py tests/unit/test_spool_store_switch.py tests/unit/test_stages_candidates_select.py tests/unit/test_stages_conflict_rerun_inputs.py tests/unit/test_stages_flake_coverage.py tests/unit/test_stale_running.py tests/unit/test_supervise_idle_point.py tests/unit/test_supervisor_trigger.py tests/unit/test_ticket_lint_rules.py tests/unit/test_ticket_write_consumers_author.py tests/unit/test_ticket_write_consumers_runner.py` passes with the migrated tests keeping their names and assertions, so a test that asserted a Git call still asserts the same call (now via `fake.calls`), not a weaker one.

## Verification
```
./dev.py test tests/integration/test_git_fake_adoption.py
./dev.py test tests/unit/test_runner_attempt_manifest.py tests/unit/test_runner_terminal_removal_shield.py tests/unit/test_serve_idle_poll.py tests/unit/test_spool_store_switch.py tests/unit/test_stages_candidates_select.py tests/unit/test_stages_conflict_rerun_inputs.py tests/unit/test_stages_flake_coverage.py tests/unit/test_stale_running.py tests/unit/test_supervise_idle_point.py tests/unit/test_supervisor_trigger.py tests/unit/test_ticket_lint_rules.py tests/unit/test_ticket_write_consumers_author.py tests/unit/test_ticket_write_consumers_runner.py
```

## Definition of rejected
A change under `clutch/`; a migrated test whose assertion is dropped, weakened or turned into one that also passes when the call never happens; a stand-in left in a migrated file; a file outside the Scope fence edited; `GitFake` members that differ from `Git` in name or signature.

## Time budget
- expected: 26m
- stuck: 52m
