---
state: draft
source: human
priority: P0
kind: bug
---

## Depends on
none

## Context
- tests/unit/test_serve_idle_poll.py
- tests/integration/test_serve_parallel_admission.py
- tests/integration/serve_rig.py
- clutch/runner.py
- tickets/serve-verdicts-wait-for-runs/evidence/serve-verdict-latency.txt

## On-demand
- clutch/serve.py
- clutch/daemon.py
- docs/how-clutch-works.md

## Goal / Why
A confirm or reject sent to a running `clutch engine serve` is applied only after every running implementation finishes, and while it waits the engine admits no new run. On 2026-11-21 a confirm submitted at 07:09:24Z was applied at 07:15Z, when the running ticket ended, and no second ticket started in between although three confirmed tickets with disjoint fences were queued. With `scheduler.parallel` `max_runs` 2 and an operator confirming every few minutes, serve behaves like one run at a time for much of the time. The evidence file has the timeline and the cause.

Cause: the merge poll in `clutch/serve.py` (`merge`) takes one exclusive section (`self.mutations()`, which is `admission.exclusive()`) for two jobs, applying verdicts (`control.inbox.settle_admissions(self.apply_verdict)`) and processing the merge queue. `exclusive()` waits until no run holds a slot and, while it waits, `_acquire_run` refuses new runs. Both jobs commit to the main checkout, so they must not overlap each other. Verdict application does not touch an implementation, which runs in its own worktree, so it has no reason to wait for one.

After this ticket a confirm or reject request is applied without waiting for running implementations to finish, and a verdict waiting to be applied never blocks admission of a ready ticket. The merge queue keeps its exclusion from implementations exactly as today.

## Boundary contract
### Serve verdict settlement
- disposition: extend
- owner: clutch/serve.py (the `merge` poll and `apply_verdict`)
- consumers: `clutch ticket confirm`, `clutch ticket reject` and `clutch box triage` requests published to a running serve; the VS Code extension's confirm and reject actions
- observable change: verdict requests are settled in a section that excludes the merge queue's processing and delivery (and the other main-checkout writers named in Scope in) but does not wait for running implementations and does not count as an exclusive waiter for admission
- compatibility: the same ticket-plane commits, journal signals, `verdict_refused` events and exit behavior as today for each verdict, in the same order of arrival; merge processing, delivery, retro and upgrade handling keep today's exclusion; `max_runs` 1 behaves as before
- acceptance: criteria 1 to 5
- tests: tests/unit/test_serve_verdict_settle.py and tests/integration/test_serve_verdict_latency.py
- post-merge source of truth: clutch/serve.py and docs/how-clutch-works.md section 7.2

## Scope in / Scope out
Scope in:
- `clutch/serve.py`: split the merge poll's body. Verdict settlement (`self.control.poll()` for the inbox and `settle_admissions(self.apply_verdict)`) runs under a new `asyncio.Lock` owned by `Serve` (the repo lock), not under `mutations()`. Every other place that commits to the main checkout while serve runs takes the same lock around that commit: the merge queue's `process()` and delivery (still inside `mutations()` as today, with the repo lock taken inside it), and the watcher's `scan` intake commit. The implementer reads `clutch/serve.py`, `clutch/daemon.py` and `clutch/runner.py` and lists, in the run record, each site that commits to the main checkout or rewrites a ticket file, and the lock each now takes; a site that cannot overlap verdict application is named with the reason. `merge_work()` keeps returning True for a pending verdict so the poll still reaches the verdict step; the poll takes `mutations()` only when merge-queue or retro or upgrade work exists, not for a verdict alone.
- `docs/how-clutch-works.md` section 7.2: replace the sentence that says a poll with work excludes running implementations until it finishes: a verdict is applied beside running implementations; merge-queue processing and delivery still exclude them. After editing, run `uv run clutch meta refresh docs/how-clutch-works.md` and change nothing else in its header.
- `tests/unit/test_serve_idle_poll.py`: the one expectation that changes is the case where a verdict alone is "work": it no longer enters `mutations()`; it takes the repo lock. Nothing else there changes.
- New tests, each file starting with a `clutch:meta` header created by `uv run clutch meta refresh <file>` with only the `purpose` line edited by hand: `tests/unit/test_serve_verdict_settle.py`, `tests/integration/test_serve_verdict_latency.py`, and the reproducer `tests/regress_serve_verdict_latency.py` that `## Regression` names. Import `tests/integration/serve_rig.py` and change nothing in it.

Scope out: the watcher's own exclusive gate and the box-intake poll (unchanged); merge-queue admission rules, `fill_slots`, `max_unmerged`; `clutch/daemon.py` unless the reproducer still fails after the `serve.py` change (then say what failed in the run record); `clutch/runner.py::apply_admission` itself; any change to what a verdict does; `config.yaml`.

## Scope fence
- clutch/serve.py
- clutch/daemon.py
- docs/how-clutch-works.md
- tests/unit/test_serve_idle_poll.py
- tests/unit/test_serve_verdict_settle.py
- tests/integration/test_serve_verdict_latency.py
- tests/regress_serve_verdict_latency.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_serve_verdict_latency.py` runs serve through `tests/integration/serve_rig.py` with `max_runs` 2 and one implementation blocked on a release event. A confirm for a draft ticket published while it is blocked is applied (the `clutch(<stem>): confirmed` commit exists and the `draft_confirmed` signal is journaled) before the blocked implementation is released, within 5 seconds of the fake clock, not after it ends.
2. The same test shows that while that confirm waits to be applied, a second ready ticket with a disjoint fence is admitted and starts its implementation, so two implementations overlap; the old behavior starts it only after the first ends. Check: `./dev.py test tests/integration/test_serve_verdict_latency.py`.
3. The same test shows a reject request published during a blocked run is applied the same way, a refused verdict (a stem that is not a draft or in the Reject queue) still journals `verdict_refused` with the same reason as today, and a stop request published at the same time is still honored, not dropped.
4. `./dev.py test tests/unit/test_serve_verdict_settle.py` shows verdict settlement and merge-queue processing never run at the same time: with a stand-in whose merge-queue `process()` is blocked, a pending verdict is not applied until it finishes, and the reverse; and a verdict alone enters the repo lock, not `mutations()` (a counting stand-in for `admission.exclusive` is entered 0 times for a verdict-only poll, not once).
5. `./dev.py test tests/unit/test_serve_idle_poll.py tests/integration/test_serve_parallel_admission.py tests/integration/test_serve_admission.py tests/unit/test_admission_parallel_run_set.py` still passes, with the one case named in Scope in changed in `tests/unit/test_serve_idle_poll.py` and nothing else edited there.
6. `uv run python tests/regress_serve_verdict_latency.py` prints `{"regression_result": "pass"}` and exits 0 on the fixed branch and `{"regression_result": "defect"}` with a non-zero exit on the merge base, as `## Regression` states.
7. `uv run clutch meta check tests/unit/test_serve_verdict_settle.py tests/integration/test_serve_verdict_latency.py tests/regress_serve_verdict_latency.py docs/how-clutch-works.md` exits 0 (only the files this ticket creates or edits).

## Verification
```
./dev.py test tests/integration/test_serve_verdict_latency.py tests/unit/test_serve_verdict_settle.py tests/unit/test_serve_idle_poll.py tests/integration/test_serve_parallel_admission.py tests/integration/test_serve_admission.py tests/unit/test_admission_parallel_run_set.py
```

## Definition of rejected
A verdict applied at the same time as the merge queue's processing or delivery, or as the watcher's intake commit; a confirm or reject that commits something different from today, in a different order, or loses a `verdict_refused`; a stop or kill request that is dropped or delayed longer than today; merge processing, retro or upgrade handling allowed to overlap a running implementation; the regression reproducer passing on the merge base; a test or fixture added to `tests/integration/serve_rig.py` or another hot test file.

## Time budget
- expected: 30m
- stuck: 60m
- reason: one cause in one poll, a lock added around the existing main-checkout commit sites, one test file per layer and one reproducer

## Regression
```
uv run python tests/regress_serve_verdict_latency.py
```
- carries: tests/regress_serve_verdict_latency.py
