---
state: draft
source: human
priority: P0
kind: bug
---

## Depends on
- ticket-writes-atomic-commit

## Context
- clutch/serve.py
- clutch/daemon.py::DaemonTasks
- clutch/control.py::ControlInbox
- tests/integration/test_serve_parallel_admission.py
- tests/integration/serve_rig.py
- tests/unit/test_serve_idle_poll.py
- tickets/serve-confirm-during-check/evidence/confirm-delay-evidence.json
- docs/how-clutch-works.md#7.2

## Goal / Why
Apply accepted confirmations while unrelated tickets are still in Implement, Check or Review. On November 21 the attached request was accepted at 10:33:19Z and applied at 10:36:22Z, 183 seconds later, after the unrelated Check/Review released its run slot. The merge consumer owns settlement under admission.mutations(), which waits for all slots. This is the observed instance correction. Its prerequisite supplies the atomic ticket-write boundary that the earlier rejected serve-verdicts-wait-for-runs proposal lacked. Preserve the existing request effects and commit semantics, not just faster acceptance messages.

## Boundary contract
### Serve admission-request settlement
- disposition: extend
- owner: clutch/serve.py and clutch/control.py::ControlInbox.settle_admissions
- consumers: CLI and extension confirm/reject requests submitted to live serve
- observable change: accepted verdicts settle in their own owned worker, independently of merge polling and run-slot quiescence; settlement waits only for a real conflicting checkout write transaction
- compatibility: preserve lifecycle matching, exactly-once request effects, refusals, running-ticket protection, actor/reason forwarding and commit contents; merge/check/retro run exclusion remains unchanged
- acceptance: real confirmation commit and draft_confirmed signal occur before a held Check is released; merely recording accepted does not pass
- tests: tests/unit/test_serve_verdict_worker.py and tests/integration/test_serve_confirm_during_check.py
- post-merge source of truth: clutch/serve.py and journaled request completion

### Owned worker lifecycle
- disposition: extend
- owner: clutch/daemon.py::DaemonTasks and clutch/serve.py
- consumers: serve startup, heartbeat/failure observation, stop/kill and upgrade teardown
- observable change: add a required verdict_consumer callback to DaemonTasks and its owned task set; Serve adds verdicts() and its responsiveness member; include the worker in cancellation, exception observation and join before engine-lock release
- compatibility: existing consumer constructor callers migrate together; preserve the indexes of existing Serve workers by appending the new consumer; no detached task or optional compatibility branch
- acceptance: new worker failure and stop/kill unwind are observed and awaited; no work starts during construction
- tests: tests/integration/test_serve_lifecycle.py and tests/integration/test_daemon_tasks.py
- post-merge source of truth: clutch/daemon.py::DaemonTasks and clutch/serve.py

## Scope in / Scope out
Scope in:
- Move control.poll and settle_admissions from the merge transaction to a dedicated Serve.verdicts worker. Reuse the current polling interval, Responsiveness and ControlInbox owners; do not create a second request store, an ad hoc timer or another lock. Remove verdict-only entries from merge_work so an accepted confirmation never reserves an exclusive run waiter. The worker uses the prerequisite's already-protected actual ticket writers, never admission.exclusive or mutations.
- Do not merely move settlement earlier in merge(): that consumer can already be blocked waiting for a run or processing a merge when a request arrives. Verify the new worker still settles a confirmation when merge processing was queued before the request, and while another ticket is held in Check.
- Extend DaemonTasks with the required appended verdict_consumer argument, migrating Serve and every constructor in tests/integration/test_daemon_tasks.py, test_kill_failure_suppression.py and test_kill_worker_stop.py. Extend Serve responses, health observation and shutdown membership; update worker-count assertions in test_serve_lifecycle.py and test_daemon_tasks.py, without changing the existing component indexes. Add new tests in their own files.
- Update only the two existing worker/task-count assertions in tests/integration/test_daemon_composition.py from four workers/three consumers to five workers/four consumers, and the existing worker-count assertion in tests/integration/test_daemon_soak_runner.py from four to five. The first file is hot: add no test, fixture or helper and change no other behavior there.
- In test_serve_idle_poll.py migrate only the decision/inbox merge-work rows and necessary worker fixture fields: these no longer request mutations. In test_serve_parallel_admission.py change test_dispatch_consumed_confirm_and_stop to require confirmed before releasing the held run; retain the stop and exactly-once assertions.
- Add an event-controlled integration test using the existing serve rig without editing it. Hold a real Check stage, submit through publish_request, and observe the committed ticket state plus draft_confirmed and request EFFECT_COMPLETION before release. Exercise a queued merge, reject/refusal, a second eligible disjoint ticket and stop/kill. Use fake clock/events, never a sleep-until-it-passes timing test.
- Add the carried regression command that runs this real composition scenario on old and new code, emits exactly the regression_result JSON protocol, and treats missing prerequisites as error. Missing the new worker/API on base is not the defect oracle; failure to confirm before releasing Check is.
- Update the control/serve documentation and existing confirm/reject help text to distinguish acceptance from applied completion and explain that active Check/model work does not delay ticket-only verdicts. No new CLI verb or setting.
Scope out:
- No merge-gate weakening, extra writer lock, synchronous CLI wait flag, stop/restart workaround, timer tuning, direct ticket editing by the CLI around the engine, or changes to triage policy.

## Scope fence
- clutch/serve.py
- clutch/daemon.py
- clutch/__main__.py
- clutch/help.py
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- tests/unit/test_serve_verdict_worker.py
- tests/unit/test_serve_idle_poll.py
- tests/integration/test_serve_confirm_during_check.py
- tests/regress_serve_confirm_during_check.py
- tests/integration/test_serve_parallel_admission.py
- tests/integration/test_serve_lifecycle.py
- tests/integration/test_daemon_tasks.py
- tests/integration/test_kill_failure_suppression.py
- tests/integration/test_kill_worker_stop.py

- tests/integration/test_daemon_composition.py
- tests/integration/test_daemon_soak_runner.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_serve_confirm_during_check.py` proves applied confirmation, commit and exactly one completion while Check remains held, including when the merge consumer is already waiting for quiescence; the old accepted-but-draft outcome fails.
2. `./dev.py test tests/unit/test_serve_verdict_worker.py tests/integration/test_serve_confirm_during_check.py` proves verdict-only work acquires no admission-exclusive waiter, preserves reject/refusal and stop semantics and does not block a disjoint ready ticket's admission.
3. `./dev.py test tests/integration/test_serve_lifecycle.py tests/integration/test_daemon_tasks.py tests/integration/test_kill_failure_suppression.py tests/integration/test_kill_worker_stop.py` proves the new consumer is owned, monitored and joined before shutdown returns, preserving existing worker indexes.
4. `.venv/bin/python tests/regress_serve_confirm_during_check.py` returns pass at head and defect on base using the same event-controlled externally observable confirmation behavior; missing setup is error.

## Verification
```
./dev.py test tests/unit/test_serve_verdict_worker.py tests/unit/test_serve_idle_poll.py tests/integration/test_serve_confirm_during_check.py tests/integration/test_serve_parallel_admission.py tests/integration/test_serve_lifecycle.py tests/integration/test_daemon_tasks.py tests/integration/test_kill_failure_suppression.py tests/integration/test_kill_worker_stop.py tests/integration/test_daemon_composition.py tests/integration/test_daemon_soak_runner.py
```

## Definition of rejected
Confirmation still waits for unrelated run release; only its acceptance message changes; settlement races a main-checkout write; a new worker is detached or unobserved; or existing merge/stop/kill protection is bypassed.

## Time budget
- expected: 25m
- stuck: 50m

## Regression
```
.venv/bin/python tests/regress_serve_confirm_during_check.py
```
- carries: tests/regress_serve_confirm_during_check.py
- carries: tests/integration/test_serve_confirm_during_check.py
