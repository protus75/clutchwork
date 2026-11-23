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
- clutch/serve.py::Serve.scan
- clutch/serve.py::Serve.verdicts
- clutch/serve.py::Serve.maintenance
- tests/integration/serve_rig.py

## Goal / Why
Serve stopped with `CommitLockTimeout` on 2026-11-22 at 05:23:29Z, 05:27:38Z and 05:50:19Z. The first worker failure at 05:23:20Z names a lock held by Serve's own PID since 05:21:29Z. It does not identify the worker or record a traceback. The concurrent `shared-git-fake` stage start does not identify the failing operation. The batch hold is addressed separately by `intake-commit-lock-per-ticket`.

Contain a recoverable lock acquisition failure at a real Serve work boundary. An owned callback may already have accepted work or made durable progress before the exception. Test the actual lock acquisition and the operation's custody before selecting the retry point. Preserve unrelated runs, and log which operation timed out so a later incident can identify the failing path.

## Boundary contract
### Serve commit-lock timeout recovery
- disposition: extend
- owner: clutch/serve.py
- consumers: the Serve work loop, the owning consumer and engine diagnostics
- observable change: a commit-lock acquisition timeout at a proven retryable boundary while Serve is active records the operation, returns it to its existing retry point and lets other runs continue
- compatibility: other failures and stop or kill keep their existing handling. Preserve ownership of journaled or pending work and existing dispatch containment
- acceptance: force the lock wait at the production operation and verify the owned item completes once after the lock is released
- tests: `tests/unit/test_serve_commit_lock_timeout.py` with an existing Serve rig and fake platform or Git seam
- post-merge source of truth: clutch/serve.py

## Scope in / Scope out
Scope in:
- Trace the real Serve operations that acquire the commit lock and can escape a consumer, including `Serve.scan` intake and `Serve.verdicts` settlement. The ticket dispatch callback already has per-ticket exception containment. The maintenance call runs outside `guarded`. Record which acquisition site the regression drives and how it reaches engine failure on main. If the historical worker cannot be established from evidence, label the reproduced route separately from the historical incident.
- Contain the timeout around the concrete operation that the regression reproduces, at the smallest existing retry boundary whose input is still owned or durably recoverable. Use the next poll or existing effect retry rather than restarting an arbitrary callback. Log `commit_lock_timeout` with the operation and preserve stop or kill behavior. For a verdict, prove the same accepted request settles via its existing durable effect key. For a scan, prove a still-pending ticket reaches intake exactly once after the lock clears.

- Create `tests/unit/test_serve_commit_lock_timeout.py` for the concrete acquisition and ownership cases above. Reuse the Serve rig and the existing fake seams.

Scope out: long-hold prevention, changing the wait deadline, retrying every consumer, new knobs and new durable work queues.

## Scope fence
- clutch/serve.py
- tests/unit/test_serve_commit_lock_timeout.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_serve_commit_lock_timeout.py` drives an actual Serve consumer to a commit-lock acquisition and recreates worker failure on main. A test that raises a timeout from an arbitrary stub consumer is insufficient.
2. The same test proves the consumer remains alive with another run active, logs `commit_lock_timeout` naming the operation, and completes the same pending item exactly once after the lock is released. It fails if the item is dropped, committed twice or stops Serve.
3. The same test covers an ordinary consumer exception and a stop or kill already requested. Neither is converted into a timeout retry. `./dev.py test tests/integration/test_serve_lifecycle.py tests/unit/test_serve_dispatch_containment.py` continues to pass.

## Verification
```
./dev.py test tests/unit/test_serve_commit_lock_timeout.py tests/integration/test_serve_lifecycle.py tests/unit/test_serve_dispatch_containment.py
```

## Definition of rejected
A branch that generically restarts a whole consumer after partial work, loses the producing item, repeats a committed effect, retries while stopping, swallows other failures, or tests only an invented callback without a real lock acquisition boundary.

## Time budget
- expected: 25m
- stuck: 50m
