---
state: draft
source: human
priority: P1
kind: bug
---

## Depends on
none

## Runs before
- serve-confirm-during-check

## Context
- clutch/serve.py::Serve.scan
- clutch/serve.py::Serve.watch
- clutch/serve.py::Serve.intake_snapshot
- clutch/daemon.py::DaemonAdmission
- clutch/scheduler.py::Scheduler.dispatch_next
- clutch/watcher.py::Watcher
- clutch/tickets.py::intake
- clutch/git.py::Git.commit_edit
- tests/unit/test_serve_idle_poll.py
- tests/unit/test_admission_parallel_run_set.py::test_watch_publication_excludes_runs
- tests/regress_serve_parallel_admission.py
- tickets/serve-scan-watch-off-exclusive/evidence/serve-scan-watch-exclusive.txt

## On-demand
- docs/how-clutch-works.md

## Goal / Why
A ticket-file change (new draft, supervisor rework edit, operator edit) makes serve's second implementation slot wait for the running ticket. `Serve.scan` enters `mutations()` (`admission.exclusive()`) whenever its intake snapshot changes, and `Serve.watch` holds `admission.exclusive()` while it publishes changed tickets. `exclusive()` waits until `_holding == 0` and, while it waits, `_acquire_run` refuses new runs, so with `scheduler.parallel` `max_runs` 2 serve runs one implementation at a time for much of the time (the owner's confirm submitted 10:58:51Z applied only at 11:05Z with no second ticket started; see the evidence file). The merged chain `git-commit-edit-owner`, `runner-ticket-writes-commit-edit`, `rework-ticket-writes-commit-edit`, `author-ticket-writes-commit-edit` and `ticket-write-serialization-proof` already made every engine write of a ticket file plus its commit one `Git.commit_edit` section under `main_write()` and the commit lock, and `intake` holds both locks for its whole body. The two serve sections now exclude only what those locks already exclude, so they need no run-wide exclusion.

What each section does and what it can race, from the code:
- `scan`: runs `intake(...)` (holds `main_write()` and the commit lock across status, stray check, stamps and commits; its journal append has its own lock), then reads every ticket and re-snapshots. Its writers are the engine ticket writers (all `commit_edit`, serialized with intake by those locks), the merge queue's squash (`merge_squash` takes `main_write()`), and the exclusive sections that still run beside it (retro, supervise, box intake, verdict settlement, maintenance). Intake's pending set is only `tickets/<stem>/ticket.md` files (`_pending`/`_is_ticket_path`) and its stray check counts only staged paths, which exist only inside a commit-lock section, so an unstaged `lift_outbox` or retro file write is never adopted. The one unserialized step is the post-intake read of ticket files and re-snapshot, which can see a `commit_edit` callback's stamped but uncommitted bytes.
- `watch`: yields changed stems to `Watcher.run`, whose debounce task reads, parses and publishes with no await between read and `Scheduler.update` (a synchronous dict assignment). The only await-point race is `Scheduler.dispatch_next`, which reads `pending`, awaits, then pops the selected stem; a publication of that stem inside the window is lost to the pop. `dispatch_next` holds `Scheduler._slot` for exactly that window and releases it when the run task is created, so `_slot` is the lock that excludes the race. Today's `exclusive()` never covered that window: it waits for runs, not for a selection in flight.

After this ticket neither section waits for a running implementation or counts as an exclusive waiter. The intake commit stays serialized by the locks it already takes, the post-intake read takes `main_write()`, and publication holds `_slot`.

Out of scope: verdict settlement in the merge poll (`settle_admissions`/`apply_verdict`, which is what applies a confirm) belongs to the confirmed ticket `serve-confirm-during-check`, which this ticket runs before; retro, supervise/triage/calibrate, box intake, maintenance and startup keep `mutations()`/`exclusive()`. The implementer names in the run record which of these still take an exclusive section and why this ticket leaves them.

## Boundary contract
### Serve watcher intake and publication
- disposition: extend
- owner: clutch/serve.py (`Serve.scan`, `Serve.watch`)
- consumers: ticket intake and publication for every new or edited ticket file, the scheduler's pending set, and every writer that reaches the engine through a ticket-file commit (`clutch ticket confirm|reject`, the roadmap driver, Author, Rework)
- observable change: `scan` and `watch` never enter `admission.exclusive()` or `mutations()`, so a ticket-file change never waits for a running implementation and never blocks `_acquire_run`; `scan` reads tickets and re-snapshots under `git.main_write()`; `watch` holds `core.scheduler._slot` across publication
- compatibility: restores the behavior the parallel design states (`max_runs` slots admitted beside intake); intake's commits, journal events, published set, debounce and the stop check are preserved; with `max_runs` 1 behavior is unchanged
- acceptance: criteria 1 to 6
- tests: tests/unit/test_serve_scan_watch_locks.py, tests/integration/test_serve_scan_watch_overlap.py
- post-merge source of truth: clutch/serve.py and docs/how-clutch-works.md section 7.2

### Admission exclusion for other serve sections
- disposition: reuse
- owner: clutch/daemon.py::DaemonAdmission
- consumers: retro, supervise, box intake, maintenance, startup, and verdict settlement until `serve-confirm-during-check` moves it
- observable change: none; `exclusive()` and `mutations()` are unchanged
- compatibility: every other caller keeps today's exclusion, and `clutch/daemon.py` is not edited
- acceptance: criterion 5
- tests: tests/unit/test_admission_parallel_run_set.py
- post-merge source of truth: clutch/daemon.py::DaemonAdmission

## Scope in / Scope out
Scope in:
- `clutch/serve.py` `scan`: drop `async with self.mutations()`. Keep `if self.stopping: return {}` ahead of `intake`. Call `intake` unlocked (it takes both locks itself; wrapping it in `main_write()` would deadlock). Then `async with self.checkout.git.main_write():` around `self.scanned = ...` and the post-intake `intake_snapshot()`.
- `clutch/serve.py` `watch`: replace `self.core.admission.exclusive()` with `self.core.scheduler._slot`, acquired and released through `response.wait` as the gate is today, held across the yields and the `_waits` gather. Hold it only there; never across a run or an await on admission.
- `docs/how-clutch-works.md` section 7.2 (the Dispatch bullet): the sentence "Startup, sweeps and changed watch publication also exclude slot-holding runs" no longer names changed watch publication; say intake and publication proceed beside running implementations. Then `uv run clutch meta refresh docs/how-clutch-works.md`, changing nothing else in its header.
- Existing tests forced by the change: in `tests/unit/test_serve_idle_poll.py` the `owner` fixture gains a `main_write` lock on `git` and `core.scheduler` with a `_slot` lock, `test_scan_inputs_and_own_writes` and `test_pending_stem_state_retries_intake` expect `owner.entries == []` where they expect `["mutations", "exclusive"]` today, and `test_watch_changed_publication_enters_once` expects `[]` where it expects `["exclusive"]`; the other cases of that file, including the merge and box cases, are unchanged. `tests/unit/test_admission_parallel_run_set.py::test_watch_publication_excludes_runs` is replaced by the new behavior (a dispatch starts while publication is held) and its `owner` gains `core.scheduler`; its other cases are unchanged. `tests/regress_serve_parallel_admission.py` builds `owner.checkout.git` with only `status_porcelain` and `rev_parse`, so it gains a `main_write` lock; its assertion is unchanged.
- New tests, each starting with a `clutch:meta` header from `uv run clutch meta refresh <file>` with only `purpose` edited by hand (if the serve lock blocks the refresh, the implementer creates the header): `tests/unit/test_serve_scan_watch_locks.py`, `tests/integration/test_serve_scan_watch_overlap.py` and the reproducer `tests/regress_serve_scan_watch_off_exclusive.py`. Import `tests/integration/serve_rig.py` and change nothing in it.

Scope out: verdict settlement (owned by `serve-confirm-during-check`), retro, supervise, box intake, maintenance and startup are not changed here; `clutch/daemon.py`, `clutch/scheduler.py`, `clutch/tickets.py`, `clutch/git.py`, `clutch/runner.py`; what intake does to a ticket; the `test_merge_work` decision rows and `tests/integration/test_serve_parallel_admission.py::test_dispatch_consumed_confirm_and_stop`, which pin verdict settlement and are `serve-confirm-during-check`'s to change. The existing `tests/integration/test_serve_scan_head.py` is not edited. If the implementer finds a site that cannot be safe without exclusion, keep that one site exclusive, name it and the reason in the run record, and the criteria still hold for every other site.

## Scope fence
- clutch/serve.py
- docs/how-clutch-works.md
- tests/unit/test_serve_idle_poll.py
- tests/unit/test_admission_parallel_run_set.py
- tests/regress_serve_parallel_admission.py
- tests/unit/test_serve_scan_watch_locks.py
- tests/integration/test_serve_scan_watch_overlap.py
- tests/regress_serve_scan_watch_off_exclusive.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_serve_scan_watch_overlap.py` runs serve through `tests/integration/serve_rig.py` with `max_runs` 2 and one implementation blocked on a release event. A new draft ticket committed to main while it is blocked is intaken and published, and a second ready ticket with a disjoint fence starts while the first is still blocked, so two implementations overlap; the test advances the fake clock past `SERVE_POLL_S` and never sees `admission.exclusive_pending()` true. The wrong result it rules out: the second ticket starting only after the first is released.
2. `./dev.py test tests/integration/test_serve_scan_watch_overlap.py` also edits a ticket file while a run is held and shows the scheduler's pending set holds the new content, and that a stop request made then is still honored, not dropped.
3. `./dev.py test tests/unit/test_serve_scan_watch_locks.py` shows with one run holding a slot that a changed-snapshot `scan` enters `mutations()` and `exclusive()` 0 times and reads tickets while `main_write()` is held, that `watch` publication holds `core.scheduler._slot` and enters `exclusive()` 0 times, and that a stand-in `dispatch_next` selection and a publication never interleave. Wrong results ruled out: one entry into either gate, or a read outside `main_write()`.
4. `./dev.py test tests/unit/test_serve_scan_watch_locks.py` shows `scan` returns `{}` without calling `intake` when `stopping` is set, not an intake commit after a stop.
5. `./dev.py test tests/unit/test_serve_idle_poll.py tests/unit/test_admission_parallel_run_set.py tests/integration/test_serve_parallel_admission.py tests/integration/test_serve_scan_head.py tests/integration/test_serve_admission.py` passes, with only the cases named in Scope in changed; the merge and box cases of `tests/unit/test_serve_idle_poll.py` are not edited by this ticket.
6. `uv run python tests/regress_serve_scan_watch_off_exclusive.py` prints `{"regression_result": "pass"}` and exits 0 on the fixed branch, and prints `{"regression_result": "defect"}` with a non-zero exit on the merge base.
7. `uv run clutch meta check tests/unit/test_serve_scan_watch_locks.py tests/integration/test_serve_scan_watch_overlap.py tests/regress_serve_scan_watch_off_exclusive.py docs/how-clutch-works.md` exits 0.

## Verification
```
./dev.py test tests/integration/test_serve_scan_watch_overlap.py tests/unit/test_serve_scan_watch_locks.py tests/unit/test_serve_idle_poll.py tests/unit/test_admission_parallel_run_set.py tests/integration/test_serve_parallel_admission.py tests/integration/test_serve_scan_head.py tests/integration/test_serve_admission.py
```

## Definition of rejected
`scan` or `watch` waiting for `_holding == 0` or counting as an exclusive waiter; a new lock type, a DuckDB state or a dual path beside the old gate; `intake` called inside `main_write()` (deadlock); a ticket read after intake outside `main_write()`; publication outside `_slot`; a stop or kill request dropped or delayed longer than today; an edit to `clutch/daemon.py` or `tests/integration/serve_rig.py`; the reproducer passing on the merge base.

## Time budget
- expected: 30m
- stuck: 60m
- reason: two sections in one file, locks that already exist, one test per layer and one reproducer

## Regression
```
uv run python tests/regress_serve_scan_watch_off_exclusive.py
```
- carries: tests/regress_serve_scan_watch_off_exclusive.py
