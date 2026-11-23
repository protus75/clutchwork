---
priority: P0
kind: feature
agent_tier: medium
agent_effort: medium
source: box:suggestion
state: confirmed
---

## Depends on
none

## Context
- clutch/tickets.py::intake
- tests/unit/test_intake_lock_order.py

## Goal / Why
On 2026-11-22 (05:23Z and 05:27Z) serve stopped twice with `CommitLockTimeout` (box-001081). `Serve.scan` calls `tickets.intake(stems=None)`. `intake` enters `git._commit_lock` once, outside the `for stem in sorted(pending)` loop, and commits every pending ticket inside that single hold. About 40 `restore-*` drafts landed at once, and intake held the lock about 110 s. A running ticket's worker waited `COMMIT_LOCK_WAIT_S` (60 s) for the same lock and raised `CommitLockTimeout`. Serve treats a worker failure as fatal.

When this is done, no commit-lock hold in `intake` grows with the number of pending tickets. The status read and stray check form one hold. Each stem's plan, stamp write and commit form its own hold. The lock is released between stems, so a waiting `commit` gets it after at most one stem's commit.

Merged `intake-holds-commit-lock` added the lock but did not bound how long it is held. The open ticket `serve-commit-lock-timeout-contained` makes serve survive a timeout; it excludes hold durations, and this ticket excludes its retry and containment behaviour.

## Boundary contract
### Intake commit-lock scope
- disposition: extend
- owner: clutch/tickets.py
- consumers: `Serve.scan`, `clutch ticket` verbs that call `tickets.intake`, and any concurrent `git.commit` caller waiting on `git._commit_lock`
- observable change: the commit lock is taken once for status plus the stray check, then once per stem for plan, stamp and commit, and released between stems; `git.main_write()` stays held for the whole pass
- compatibility: `IntakeResult`, commit messages, pathspec-limited commits, journal signals, refusal behaviour and the main_write then commit-lock acquisition order are unchanged; stems are still processed in sorted order
- acceptance: with N pending tickets, a competing waiter on the commit lock acquires it between per-stem commits, and the longest single hold covers one stem's commit, not N
- tests: a new unit test with a fake git and a lock-hold recorder; the existing `tests/unit/test_intake_lock_order.py` still passes unmodified
- post-merge source of truth: clutch/tickets.py

## Scope in / Scope out
Scope in: in `clutch/tickets.py` `intake`, split the single `async with git._commit_lock` block. Hold the lock for `git.status_porcelain`, `intake_pending` and the stray raise. Then, for each stem, hold it around `_intake_plan_stem`, the stamp write, `git._commit` and the journal append. Update the `intake` docstring to say the commit lock is held per phase rather than across the whole pass. `main_write` stays an outer whole-pass guard and the stray check stays one whole-pass guard.
Scope out: serve retry or containment of `CommitLockTimeout` (`serve-commit-lock-timeout-contained`); the `COMMIT_LOCK_WAIT_S` value; other lock holders; docs.

## Scope fence
- clutch/tickets.py
- tests/unit/test_intake_commit_lock_release.py

## Acceptance criteria
1. With three pending stems and a fake `git._commit` that records `lock.locked()` on entry and exit, `./dev.py test tests/unit/test_intake_commit_lock_release.py` shows the lock is not held between consecutive stems' commits, not one continuous hold across all three.
2. A waiter that tries to acquire the commit lock while intake is committing stem two acquires it before stem three's commit starts, not after intake returns; checked by `./dev.py test tests/unit/test_intake_commit_lock_release.py`.
3. The commit order of the three stems is sorted and `IntakeResult.committed` equals all three stems, not fewer; checked by `./dev.py test tests/unit/test_intake_commit_lock_release.py`.
4. `git.main_write()` stays locked from the first status call through the last commit and a competing main_write waiter enters only after intake returns; checked by `./dev.py test tests/unit/test_intake_lock_order.py`.

## Verification
```
./dev.py test tests/unit/test_intake_commit_lock_release.py tests/unit/test_intake_lock_order.py tests/unit/test_intake_plan.py tests/unit/test_intake_scope.py
```

## Definition of rejected
The branch still commits all pending stems inside one continuous commit-lock hold, or it drops the `main_write` whole-pass guard, or it changes serve's handling of `CommitLockTimeout`.

## Time budget
- expected: 15m
- stuck: 30m
