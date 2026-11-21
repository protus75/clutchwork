---
state: draft
source: human
priority: P0
kind: bug
---

## Depends on
none

## Context
- tests/unit/test_admission_parallel_run_set.py
- tests/integration/test_serve_admission.py
- tests/integration/test_serve_driver_overlap.py
- tests/integration/serve_rig.py
- tickets/serve-polls-block-parallel-runs/evidence/serve-admission-overlap.txt

## On-demand
- clutch/daemon.py
- clutch/serve.py
- docs/how-clutch-works.md

## Goal / Why
With `scheduler.parallel: {enabled: true, max_runs: 2}` in `config.yaml`, `clutch engine serve` never runs two implementations at the same time. Across the 1659 implement runs in `engine.log`, 0 pairs overlap. On 2026-11-21 `index-config-touches` sat confirmed and queued for over an hour while `meta-fill-surface` implemented alone, with 0 `dispatch_skip` events, so the scheduler's overlap filter was not holding it. A confirm submitted during a run was not applied until the run ended. The evidence file holds the journal count and a unit reproduction against the real `DaemonAdmission`.

Cause (reproduced, see the evidence file): `DaemonAdmission.exclusive()` (`clutch/daemon.py`) waits until no run holds a slot and, while it waits, counts as an exclusive waiter, and `_acquire_run` refuses every new run while a waiter exists. `dispatch()` holds its slot for the whole run. Serve's watcher scan, merge poll and box-intake poll (`clutch/serve.py`) each enter `mutations()`, which is `exclusive()`, every `SERVE_POLL_S` (0.1 s) whether or not they have work. With one run in flight a waiter exists almost always, so a second run is never admitted, and the poll's real work (verdicts, merges, box intake, ticket intake) waits for the run to end.

After this ticket, with `max_runs: 2` and two non-overlapping confirmed tickets, serve starts the second implementation while the first is still implementing. A poll that has no work takes no exclusive section. Parallelism is a shipped 0.4.0 feature (`serve-parallel-dispatch-r1`, `-r2`) that has never worked in production, and it halves serve's throughput while it stays broken, so this runs ahead of other work.

## Boundary contract
### Serve poll admission
- disposition: extend
- owner: clutch/serve.py (the three poll loops) with `DaemonAdmission` in clutch/daemon.py
- consumers: `Serve.scan`, `Serve.merge`, `Serve.box_intake`, and through them every verdict, merge, intake and box request
- observable change: a poll loop enters `mutations()` only when a cheap check made without any lock says it has work; an idle poll takes no exclusive section, so it neither waits for a running ticket nor blocks admission of another run
- compatibility: work a poll finds is applied exactly as now, under `mutations()`, in the same order, with the same journal events; `max_runs`, `max_unmerged`, `fill_slots` and the exclusive-waiter rule that stops new admission while real maintenance waits are unchanged
- acceptance: criteria 1-4
- tests: tests/unit/test_serve_idle_poll.py and tests/integration/test_serve_parallel_admission.py
- post-merge source of truth: clutch/serve.py and docs/how-clutch-works.md section 7.2

## Scope in / Scope out
Scope in:
- `clutch/serve.py`: for each of `scan` (and the `watch` loop that calls it), `merge` and `box_intake`, name the work condition and check it before `mutations()`: `scan` enters only when ticket files or the ticket directory changed since the last scan; `merge` only when the control inbox holds a request, a stop or kill is pending, or the merge queue has pending or active work; `box_intake` only when the box has an unread host report. Each check reads state without taking the admission condition. An unavoidable false positive costs one exclusive section, never a missed event: when a check cannot tell, it returns true.
- `clutch/daemon.py`: change `DaemonAdmission` only if the reproduction in the evidence file still fails after the poll change; say in the run record what failed and why.
- `docs/how-clutch-works.md` section 7.2: replace the sentence that says maintenance excludes slot-holding runs with the rule as built: a poll with work excludes running implementations until it finishes; an idle poll does not.
- New tests only: `tests/unit/test_serve_idle_poll.py` and `tests/integration/test_serve_parallel_admission.py`, plus the reproducer `tests/regress_serve_parallel_admission.py` that `## Regression` names. Import `tests/integration/serve_rig.py` and change nothing in it.

Scope out: `scheduler.py` and `fill_slots` (the evidence shows no `dispatch_skip`, so overlap selection is not the cause); changing what exclusive work excludes, or letting a poll with real work run beside a running implementation; the scan's change detection beyond the work check; `config.yaml`; the roadmap.

## Scope fence
- clutch/serve.py
- clutch/daemon.py
- docs/how-clutch-works.md
- tests/unit/test_serve_idle_poll.py
- tests/integration/test_serve_parallel_admission.py
- tests/regress_serve_parallel_admission.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_serve_idle_poll.py` shows each of the three poll bodies, run with no work and one run holding a slot, returns without entering `mutations()`: a counting stand-in for `admission.mutations` is entered 0 times, not once. It also shows each enters it exactly once when its work condition is true.
2. `./dev.py test tests/integration/test_serve_parallel_admission.py` runs serve through `tests/integration/serve_rig.py` with `max_runs` 2 and two confirmed tickets whose fences do not overlap, with a fake implement that blocks until released. It shows the second ticket's `implement` stage_start is journaled while the first is still running (both started before either ended), not after the first ended.
3. The same test shows that with `max_runs` 1 the second ticket starts only after the first ends, and that two tickets fencing the same file still run one after the other under `max_runs` 2, not together.
4. `./dev.py test tests/integration/test_serve_parallel_admission.py` also shows that a confirm request published while one implementation is blocked is applied exactly once, with the same journal events as before, and that a stop request published then is still honored, not dropped. A poll with work still excludes running implementations until it finishes, as the Goal states.
5. `uv run python tests/regress_serve_parallel_admission.py` prints `{"regression_result": "pass"}` and exits 0 on the fixed branch and `{"regression_result": "defect"}` with a non-zero exit on the merge base, as `## Regression` states.
6. `./dev.py test tests/unit/test_admission_parallel_run_set.py tests/integration/test_serve_admission.py tests/integration/test_serve_driver_overlap.py` still passes unchanged.

## Verification
```
./dev.py test tests/unit/test_serve_idle_poll.py tests/integration/test_serve_parallel_admission.py tests/unit/test_admission_parallel_run_set.py tests/integration/test_serve_admission.py tests/integration/test_serve_driver_overlap.py
```

## Definition of rejected
A poll still enters `mutations()` when it has no work; a poll event (a verdict, merge, box report, stop or kill) can be missed or reordered; two tickets fencing the same file run at the same time; `max_runs` 1 runs two tickets; `max_unmerged` or `fill_slots` change; a test or fixture is added to `tests/integration/serve_rig.py` or another hot test file; the regression reproducer passes on the merge base.

## Time budget
- expected: 30m
- stuck: 60m
- reason: one cause across three poll loops with a shared check; splitting would leave a half-fixed serve whose second run still never starts

## Regression
```
uv run python tests/regress_serve_parallel_admission.py
```
- carries: tests/regress_serve_parallel_admission.py
