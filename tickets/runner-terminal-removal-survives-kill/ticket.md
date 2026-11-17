---
state: draft
source: box:suggestion
priority: P0
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/reconcile.py
- tests/integration/test_kill_cli_activation.py::test_killed_run_is_terminal_or_restart_reconcilable

## On-demand
- clutch/runner.py

## Goal / Why
After a run journals the `already_satisfied` terminal, a kill that lands before or during the awaited `worktree_remove` no longer leaves the ticket worktree on disk. Today `clutch/runner.py` appends the terminal, then awaits `ctx.git.worktree_remove`. A kill requested inside that journal write makes drain cancel the dispatch task, which can interrupt the removal. `reconcile.orphans` skips a stem that already has a terminal, so nothing reaps the worktree. This makes `tests/integration/test_kill_cli_activation.py::test_killed_run_is_terminal_or_restart_reconcilable[True]` fail intermittently (the assertion that the worktree is gone). It cost `merge-admission-single-owner` attempt 1 a `gate_failed` (the failure was not quarantined as a flake) and `roadmap-accept` attempt 0 a lost diff as `premise_failed`. The gate is in every ticket's run, so this is an orchestration cause. The failure mechanism is not reproduced; the fix is the shield, proved by a deterministic test.

## Scope in / Scope out
Scope in: in `clutch/runner.py`, the post-terminal worktree removal in the `already_satisfied` branch runs to completion even when the dispatch task is cancelled, and the cancellation still propagates to the caller only after the removal has completed. A bare `await asyncio.shield(...)` is not enough: its outer await raises at once, so the dispatch task ends as cancelled while the removal is still pending, and under drain the loop shutdown then cancels the orphaned inner task. The implementation must therefore shield the removal and, on `CancelledError`, wait for the inner removal task to finish and then re-raise the `CancelledError`. Add one new unit test file with a fake git whose `worktree_remove` blocks until released; the test drives the cancel and asserts the ordering below.
Scope out: `clutch/reconcile.py` (no change; do not widen `orphans`), the existing integration test (unchanged), any other terminal path, kill semantics, docs.

## Scope fence
- clutch/runner.py
- tests/unit/test_runner_terminal_removal_shield.py

## Acceptance criteria
1. With a fake git whose `worktree_remove` blocks until released, the test in `tests/unit/test_runner_terminal_removal_shield.py` cancels the task running the `already_satisfied` branch and asserts three things in order: (a) after `cancel()` and before the fake is released, the task is not done; (b) after the fake is released, awaiting the task raises `asyncio.CancelledError`; (c) when that error is raised, the fake has already recorded the removal as completed (call finished, worktree path gone from the fake's state). This rules out both an implementation that swallows the cancel and a bare shield whose outer await raises before the removal finishes. The test fails on the base commit, where the cancel interrupts the removal and the worktree stays. Check: `./dev.py test tests/unit/test_runner_terminal_removal_shield.py`.
2. The terminal `already_satisfied` state transition is appended exactly once, before the removal starts. Check: the same test asserts one transition event, not zero or two.
3. The existing kill activation test still passes in both parametrizations. Check: `./dev.py test tests/integration/test_kill_cli_activation.py`.

## Verification
```
./dev.py test tests/unit/test_runner_terminal_removal_shield.py tests/integration/test_kill_cli_activation.py
```

## Definition of rejected
The branch is thrown away if it changes `clutch/reconcile.py`, adds a retry or sleep to hide the race, edits the integration test to tolerate a surviving worktree, swallows the `CancelledError`, or shields anything beyond the post-terminal removal.

## Time budget
- expected: 25m
- stuck: 60m
