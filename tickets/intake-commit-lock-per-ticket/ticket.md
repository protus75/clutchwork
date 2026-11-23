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

## Runs before
- serve-commit-lock-timeout-contained

## Context
- clutch/tickets.py::intake
- tests/unit/test_intake_lock_order.py
- tests/unit/test_commit_lock.py

## Goal / Why
On 2026-11-22, Serve stopped repeatedly with `CommitLockTimeout` while mass intake of `restore-*` tickets was underway (Box 001081 and 001082). The engine log at 05:23:20Z records that Serve's own commit-lock hold had started at 05:21:29Z. `tickets.intake` holds that lock during the status read, a separate Git evidence query per pending stem, and the whole commit batch. Both loops keep unrelated commit writers from taking a turn.

Make the initial Git inventory a batch read and give competing commit writers opportunities to acquire the production lock between single-stem commit sections. Keep one outer `main_write` guard and the pre-write stray-staging refusal. `serve-commit-lock-timeout-contained` covers recovery after an actual wait timeout.

## Boundary contract
### Intake commit-lock scope
- disposition: extend
- owner: clutch/tickets.py
- consumers: `Serve.scan`, ticket verbs and competing Git commit writers
- observable change: one short status and evidence inventory precedes ordered per-stem commit sections, with a chance for the production polling lock's waiters to run between sections
- compatibility: preserve the whole-pass `main_write` guard, stray staging refusal before any commit, exact allowed evidence and commit paths, result and journal shapes, and sorted stem order
- acceptance: a waiter on the production `CommitLock` algorithm completes during a batch against fake platform calls and controlled time
- tests: `tests/unit/test_intake_commit_lock_release.py` and current intake tests
- post-merge source of truth: clutch/tickets.py and clutch/lockfile.py

## Scope in / Scope out
Scope in:
- In `clutch/tickets.py`, batch the Git evidence listing in `intake_pending` under the tickets path and partition results by an exact pending stem's evidence directory. Keep `_regular_evidence` checks and current treatment of staged, untracked and ignored files. Keep the admissible staged paths and pre-write refusal unchanged.
- In `intake`, keep the outer `main_write` guard. Split the initial inventory and stray check from one commit-lock section per stem. Use the existing lock and its injected scheduling seam if needed for a waiting caller to make progress. Do not rely on the fairness of `asyncio.Lock` for the process-shared commit lock. Update the intake docstring and section 10.2 of `docs/how-clutch-works.md`.
- Add a unit test using the real `CommitLock` algorithm and the fake syscall and clock setup from `tests/unit/test_commit_lock.py`, alongside fake Git commands. Update existing intake test stubs only where the batched evidence argv forces the change.

Scope out: changes to the lock wait threshold, global lock semantics or Serve's timeout handling.

## Scope fence
- clutch/tickets.py
- docs/how-clutch-works.md
- tests/unit/test_intake_commit_lock_release.py
- tests/unit/test_intake_plan.py
- tests/unit/test_intake_scope.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_intake_commit_lock_release.py` proves that a batch of pending stems takes one Git evidence inventory call and admits the same regular evidence as per-stem lookup. Include disallowed staged paths, ignored or symlink evidence, and another stem's evidence.
2. The same test holds a commit across a contender's initial poll. The contender acquires during the intake batch, before its final stem commits, with the real `CommitLock` polling algorithm and fake platform calls. A single lock hold over the batch fails the test.
3. The same test proves sorted exact-path commits and all resulting stems are recorded, and a stray staged path yields zero commits. `./dev.py test tests/unit/test_intake_lock_order.py` still checks the acquisition order and outer guard.
4. Review checks the updated lock description in `docs/how-clutch-works.md` against the implemented sections.

## Verification
```
./dev.py test tests/unit/test_intake_commit_lock_release.py tests/unit/test_intake_lock_order.py tests/unit/test_intake_plan.py tests/unit/test_intake_scope.py
```

## Definition of rejected
A branch that keeps a Git query per pending stem under the initial lock, still locks the whole batch, weakens the pre-write refusal or evidence checks, or relies on a FIFO-only fake to prove scheduling progress.

## Time budget
- expected: 25m
- stuck: 50m
