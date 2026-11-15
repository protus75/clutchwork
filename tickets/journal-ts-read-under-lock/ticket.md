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
- clutch/journal.py::Journal.append
- clutch/audit.py::audit
- tests/integration/test_journal_incremental.py

## Goal / Why
`Journal.append` renders the event `ts` from the clock (`clutch/journal.py` line 173) before it takes the `journal.lock` flock (line 179). Two writers on one journal, such as the `serve` subprocess and the test process in `tests/integration/test_host_loop.py`, can each read the clock, then take the lock in the opposite order. The later lock holder appends an earlier `ts`. `audit` then reports `segment_ts_monotonic` (`timestamp X precedes Y`), and the three `test_host_loop` tests that share the module-scoped `production` fixture error in Check (3629 passed, 3 errors on verdict-decisions-retire-on-resolution). Diagnose then handed a clean ticket to a person (`abandon-human`). After this change the timestamp is read while the lock is held, so the appended order of a segment is also its `ts` order across writers.

This is the orchestration-cause fix. Its test failure is intermittent, so criterion 1 uses a deterministic lock-held check on the clock call instead of a race.

## Scope in / Scope out
Scope in: in `Journal.append`, call `self._clock()` and `render_ts` after `fcntl.flock(lock_fd, fcntl.LOCK_EX)` succeeds, and build `event` and `data` from that value inside the locked region. Keep the `type`, `body`, `ticket`, `key` and signal validation before the lock. Add a unit test file `tests/unit/test_journal_ts_under_lock.py`.

Scope out: the `Violation` and `audit` logic, the `tests/integration/test_host_loop.py` tests and fixture, the test-gate floors, and any fake clock for the host-loop members (box-000395 asked for that for speed, which is a different harm). Do not change the `ts` format or the segment roll logic. If the clock read moves, the only forced edit is moving the `event`/`data` construction below the flock.

## Scope fence
- clutch/journal.py
- tests/unit/test_journal_ts_under_lock.py

## Acceptance criteria
1. `tests/unit/test_journal_ts_under_lock.py::test_clock_read_while_lock_held` is the discriminating test. It passes a probe clock that opens `<state>/journal.lock` with `O_CREAT`, tries `fcntl.flock(LOCK_EX | LOCK_NB)` on that fd, and records `refused` if `BlockingIOError` is raised. If the lock is taken, the probe records `not refused`, then unlocks and closes the fd before returning, so the base code cannot deadlock on append's own blocking flock. After `Journal.append`, the test asserts every recorded call is `refused` and at least one call was recorded. The base code records `not refused`, so the assertion fails there. It does not hang.
2. `tests/unit/test_journal_ts_under_lock.py::test_ts_follows_append_order_across_handles` is a preservation test and also passes on the base commit. It appends alternately through two `Journal` handles on one state dir with one shared increasing clock. `[e.ts for e in journal.read()]` equals its own `sorted()` and `audit_journal(journal)` returns `[]`, not a `segment_ts_monotonic` violation. It checks that moving the clock read keeps two-handle append order and a clean audit.
3. `tests/unit/test_journal_ts_under_lock.py::test_invalid_event_never_reads_clock` calls `append` with a non-emittable type and asserts `ValueError` while the clock call count stays 0.
4. `./dev.py test tests/integration/test_journal.py tests/integration/test_journal_incremental.py tests/integration/test_journal_roll.py tests/integration/test_audit.py` exits 0.
5. `./dev.py test tests/integration/test_host_loop.py` exits 0 with 0 errors on 3 consecutive runs.

## Verification
```
./dev.py test tests/unit/test_journal_ts_under_lock.py
./dev.py test tests/integration/test_journal.py tests/integration/test_journal_incremental.py tests/integration/test_journal_roll.py tests/integration/test_audit.py
./dev.py test tests/integration/test_host_loop.py
```

## Definition of rejected
The branch is rejected if it adds a fake clock, a retry, a skip or xfail on the host-loop tests, loosens `segment_ts_monotonic`, or changes the `ts` format, instead of fixing where the timestamp is read.

## Time budget
- expected: 25m
- stuck: 60m
