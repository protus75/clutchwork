---
state: confirmed
source: box:suggestion
priority: P0
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/lockfile.py::CommitLockTimeout
- clutch/serve.py::Serve.run
- clutch/runner.py::dispatch_exception_terminal
- tests/integration/serve_rig.py

## Goal / Why
On 2026-11-22 at 05:23:29Z serve stopped with `CommitLockTimeout`. Serve's own pid had held `commit.lock` since 05:21:29, during retro_check/preflight with about 20 concurrent requisition reviews. An implement worker's commit then waited out `COMMIT_LOCK_WAIT_S`, the exception left the worker, serve's cleanup also failed, and the whole engine stopped.

The escape path, from reading the code: `dispatch` in `clutch/serve.py` already contains any `Exception` from `callback(ticket)` (the `except Exception` that calls `dispatch_exception_terminal` and returns `infra_error`). Its two pre-callback git reads (`rev_parse` and `show`) take no commit lock, because in `clutch/git.py` only `add`, `commit` and `commit_edit` do (plus the merge and ticket-write sites). So the timeout is not escaping dispatch. It escapes an owned serve consumer, such as the merge queue, checkpoint push or maintenance, that takes the commit lock. In `Serve.run`, `guarded` treats any exception from such a consumer as fatal: it latches the failure, calls `self.stop()`, and re-raises. Cleanup then raises the latched error again, which is the second failure in the evidence. A consumer that fails this way has no stem to journal.

When this ticket is done, a `CommitLockTimeout` raised by an owned serve consumer while serve is not stopping is logged as a `commit_lock_timeout` engine-log event and that consumer is re-entered. Serve keeps running, no failure is latched, and other consumers and tickets continue. Every other exception, and any exception while stopping, still stops serve as before. The request leaves open why the lock was held so long; this ticket does not claim to fix that.

## Boundary contract
### Serve consumer failure containment
- disposition: extend
- owner: clutch/serve.py (`guarded` inside `Serve.run`)
- consumers: the serve consumer tasks, the engine log, `Serve.cleanup`, and the exit code
- observable change: a `CommitLockTimeout` from an owned consumer while `not self.stopping` and no kill is requested is logged as `commit_lock_timeout` and the consumer callback runs again. Before, it latched `pending_failure`, stopped serve, and returned exit code 1.
- compatibility: every other exception type keeps the current latch, stop and exit-code handling, and so does `CommitLockTimeout` while stopping or when a kill is requested. Dispatch containment of `callback(ticket)` exceptions is unchanged. The CLI refusal for `CommitLockTimeout` in `clutch/__main__.py` is unchanged.
- acceptance: a consumer that raises `CommitLockTimeout` once is re-entered and serve stays up
- tests: new unit test over the existing serve rig, driven by fakes
- post-merge source of truth: clutch/serve.py

## Scope in / Scope out
Scope in: in `guarded`, catch `CommitLockTimeout` when `not self.stopping` and no kill is requested, log `commit_lock_timeout` through `self.log.event`, and re-enter `callback`. Add the new unit test, which runs the changed lines in `clutch/serve.py` through the fakes of the serve rig, importing the rig from `tests/integration/serve_rig.py` without editing it and touching disk only under `tmp_path`. Because the timeout no longer reaches `Serve.cleanup`, the cleanup path is not changed.

Scope out: commit-lock hold durations, `COMMIT_LOCK_WAIT_S`, retro_check/preflight, the requisition review path, `clutch/lockfile.py`, `clutch/git.py`, `clutch/runner.py` and the drain path are unchanged. No new flag, config knob or retry counter is added.

## Scope fence
- clutch/serve.py
- tests/unit/test_serve_commit_lock_timeout.py

## Acceptance criteria
1. With the serve rig, an owned consumer whose callback raises `CommitLockTimeout` on its first call and blocks on its second keeps serve running. The consumer callback is entered twice, an engine-log event `commit_lock_timeout` is recorded, and `run()` has not returned and no exception has propagated. Checked by `./dev.py test tests/unit/test_serve_commit_lock_timeout.py`. The test must fail on the current code, where serve stops with exit code 1.
2. In the same test, a second consumer stays alive and no `worker_failure` event is logged.
3. A consumer raising `ValueError` still stops serve with exit code 1 and logs `worker_failure`, not `commit_lock_timeout`, checked by `./dev.py test tests/unit/test_serve_commit_lock_timeout.py`.
4. A `CommitLockTimeout` raised after `stop()` was requested is not re-entered and the stop completes, checked by `./dev.py test tests/unit/test_serve_commit_lock_timeout.py`.
5. The existing serve lifecycle and dispatch tests still pass: `./dev.py test tests/integration/test_serve_lifecycle.py tests/unit/test_serve_dispatch_containment.py`.

## Verification
```
./dev.py test tests/unit/test_serve_commit_lock_timeout.py tests/integration/test_serve_lifecycle.py tests/unit/test_serve_dispatch_containment.py
```

## Definition of rejected
The branch is rejected if it catches `BaseException`, swallows or re-enters a timeout while stopping, changes the lock wait or its holders, adds a retry cap, loop counter or config knob, or still stops serve when one consumer's commit-lock wait times out.

## Time budget
- expected: 25m
- stuck: 50m
