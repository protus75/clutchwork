---
state: confirmed
source: human
priority: P0
kind: bug
---

## Depends on
- serve-scan-watch-off-exclusive
- serve-confirm-during-check

## Context
- clutch/serve.py::Serve.merge
- clutch/serve.py::Serve.merge_work
- clutch/serve.py::Serve.mutations
- clutch/daemon.py::DaemonAdmission
- clutch/mergequeue.py::MergeQueue.process
- clutch/merge.py::dirty_overlap
- clutch/git.py::Git.merge_squash
- tests/unit/test_serve_idle_poll.py
- tests/unit/test_merge_dirty.py
- tests/unit/test_admission_parallel_run_set.py
- tests/regress_serve_scan_watch_off_exclusive.py
- docs/how-clutch-works.md#7.2
- tickets/serve-merge-off-exclusive/evidence/serve-merge-exclusive-evidence.txt

## Goal / Why
With `scheduler.parallel` `max_runs` 2, a reviewed ticket's merge waits for every running implementation to finish, and while it waits serve admits no new run. On 2026-11-21 `plan-prompts-priority-order` entered stage merge at 17:46:20Z and finished at 17:53:01Z (6 m 41 s) because `requisition-review-approval-reuse` held a slot until 17:52:56Z; the earlier merge of `serve-scan-watch-off-exclusive` with no implementation in flight took 3 s (evidence file). `Serve.merge` enters `self.mutations()` (`DaemonAdmission.mutations()`, which is `exclusive()`) whenever `merge_work()` is true. `exclusive()` waits for `_holding == 0` and, while it waits, counts in `_exclusive_waiters`, so `_acquire_run` refuses new runs. A merge therefore costs the second slot and the merge's own latency, which compounds the single-ticket throughput problem. This is the merge-wide implementation wait that `docs/engine-state-db-plan.md` sections 6 and 7 (row 2) name.

Why merge was exclusive: `serve-activation` (plan 19.P3) built serve single-flight with no `main_write()`, `CommitLock` or `Git.commit_edit`, and its rule was "Serialize ticket-plane mutations with the existing writer/admission boundaries so background triage, intake, and maintenance cannot race an admission". `mutations()` was the only serialization. Those locks now exist, and `docs/parallel-tickets-plan.md` already expects a `clutch/` merge to land while runs continue (section 4: a `clutch/` merge stops new admissions, then serve restarts after the runs finish).

What each action of the merge poll can race, from the code, and what already excludes it:
- Queue admission (`MergeQueue.process`, `_admit`): restore, rebase, conflict resolution and `git.add` act on `ctx.worktree(stem)` (`stages.py` line 282, one directory per stem). A ticket in merge has no running stage (its run is blocked in `AdmissionBoundary.__call__` awaiting the future), so no implementation touches that worktree. Safety and integration host commands go through `HOST_COMMAND_LOCK` (`stages.py` lines 82, 875), so they queue behind a running Check instead of overlapping it. `process()` has one caller (`Serve.merge`), so the queue's own `_slot` is uncontended.
- Squash into main (`write_squash` -> `Git.merge_squash`): holds `main_write()` and the commit lock across `git merge --squash` and the commit (`git.py` 231-235). Every other writer of the main checkout holds one of them: `commit_edit` (both), intake (both), `Git.commit` lifts at `stages.py` 600 and 632 (commit lock; their file write is under `tickets/<stem>/`, which `PostRebaseGate` keeps out of a branch, so it cannot overlap the squashed paths). A running implementation works only in its own worktree and branch; its diffs are three-dot (`main...stem`), so main advancing under it changes nothing it reads, and the queue rebases it when it reaches merge.
- Tree check after the squash (`_finish`): main may differ from the checked tree only under `tickets/` or the roadmap; a running implementation commits code only to its branch and its lifts commit only under `tickets/`, so the check holds beside runs, as it holds beside intake and verdict commits today.
- Main-checkout dirtiness check (`merge.dirty_overlap`): holds only `main_write()`, but `Git.commit` stages with `update-index` under the commit lock alone (`git.py` 107-110, 125), so a lift's staged-but-uncommitted path is visible to `git status` there and would be refused as `dirty_checkout` ("staged changes ... the squash commit would sweep in"). Today runs cannot lift during a merge poll, so this cannot happen. After this ticket it can, and a false refusal costs a rerun. `dirty_overlap` must hold the commit lock too, the order `intake` and `Git.commit_edit` use.
- Delivery (`consume_result`, `consume_conflict_rerun`, `merge.retire`, `lift_prior_diff`): writes only the merged ticket's own paths (`tickets/<stem>/attempts/<n>/prior.diff`, harvest and terminal records) under the commit lock, removes that ticket's worktree and branch with `worktree remove` plus `prune` (the same calls running stages already make beside each other at `stages.py` 556-574, 1011, 1066, 1452), and appends to the journal under its own lock. `dispatch_next` reads the journal under `Scheduler._slot` and picks a stem only when its last state is not `running`, so it cannot select the ticket mid-delivery; `scheduler.update` runs after delivery.
- `check_retro`: reads git objects and the journal only (`retro.py` `production_evidence`), and `dispatch` already calls it beside runs.
- `check_upgrade`: already called outside any section.
- Writer prune (`del self.writers[stem]`): in-memory, with no await between its test and the delete; a writer is created only after `admission.runs[stem]` exists, so a starting run is never pruned.
- `control.poll()` and any verdict settlement: after `serve-confirm-during-check` merges, settlement is its own worker; `control.poll()` is already called by `dispatch` and `maintenance` with no section.

What the exclusion still gives and must keep: the merge poll must not overlap the other exclusive sections (box intake, retro, the idle supervise pass, maintenance, startup), and serve must not consider itself idle, sweep orphans, hand off or stop-exit while a merge poll runs. Those rely on `_exclusive`, `busy()` and `mutating`, not on run quiescence. So the merge poll keeps a mutual-exclusion section but a different one: it waits only for other exclusive holders, never for `_holding`, and never counts as an exclusive waiter.

Accepted and named: a `clutch/` squash can land while a stage is mid-flight, and a stage's lazy `clutch` import then reads the new tree. The plan accepts this (new admission stops at the next `check_upgrade`; the handoff waits for idle, unchanged). `refresh_index` rewrites `index.duckdb` after a squash while a stage may read it for the related-files hint; `related_files` (`stages.py` 656-667) catches every error and returns `unavailable`, so the prompt hint degrades and nothing fails.

Not changed here: retro, the supervise pass, box intake and maintenance still exclude running implementations, and the lifts at `stages.py` 597-600 and 632 still write the file before taking the commit lock (not a `commit_edit` section); the commit lock in `dirty_overlap` is the guard this ticket needs.

## Boundary contract
### Admission merge section
- disposition: extend
- owner: clutch/daemon.py::DaemonAdmission
- consumers: `Serve.merge`; `Serve.run`, `maintenance`, `dispatch`, `abort`, `upgrade_idle` read `busy()`, `idle()` and `mutating`
- observable change: a new `merging()` section waits only for an `exclusive()` holder, never for `_holding`, never counts in `_exclusive_waiters` or `exclusive_pending()`, sets `mutating`, and makes `exclusive()` and `mutations()` wait until it exits; `busy()` is true while it is held; a second run is admitted while it is held
- compatibility: `exclusive()`, `mutations()`, `_acquire_run`, `waiting_for_merge`, `idle()` and the dispatch loop's use of `exclusive_pending()` are unchanged for every other caller; no new lock type, only one more state bit under the existing condition
- acceptance: criteria 1 and 2
- tests: tests/unit/test_admission_merging_section.py
- post-merge source of truth: clutch/daemon.py::DaemonAdmission

### Serve merge poll
- disposition: extend
- owner: clutch/serve.py::Serve.merge
- consumers: queue admission, delivery, retro check, writer prune, serve handoff and stop
- observable change: a merge poll with work no longer waits for running implementations or blocks admission of a new run; it still excludes the other exclusive sections and still marks serve busy
- compatibility: restores the parallel design (the queue admits one ticket at a time while other tickets implement); work conditions in `merge_work`, journal events, delivery order, retro check and upgrade and stop behavior are preserved
- acceptance: criteria 3, 4 and 6
- tests: tests/unit/test_serve_idle_poll.py, tests/integration/test_serve_merge_overlap.py
- post-merge source of truth: clutch/serve.py and docs/how-clutch-works.md section 7.2

### Dirty-checkout check
- disposition: extend
- owner: clutch/merge.py::dirty_overlap
- consumers: `MergeQueue._admit` (serve and inline merge)
- observable change: the status read runs under `main_write()` and the commit lock, so it never sees a path another writer has staged and not yet committed
- compatibility: findings, their codes and paved roads are unchanged; the lock order matches `Git.commit_edit` and `intake`
- acceptance: criterion 5
- tests: tests/unit/test_merge_dirty_commit_lock.py, tests/unit/test_merge_dirty.py
- post-merge source of truth: clutch/merge.py::dirty_overlap

## Scope in / Scope out
Scope in:
- `clutch/daemon.py` `DaemonAdmission`: add a `_merging` flag and `merging()`, an async context manager that waits on the existing condition for `not self._exclusive and not self._merging`, sets `_merging` and `mutating` (the current task), and on exit clears both and notifies, with the same protected release `exclusive()` uses. `exclusive()` waits for `not self._merging` as well. `busy()` is true while `_merging` is set. Do not touch `_acquire_run`, `exclusive_pending()`, `idle()` or `waiting_for_merge`.
- `clutch/serve.py` `Serve.merge`: the poll enters `self.core.admission.merging()` where it enters `self.mutations()` today. Keep `merge_work`, `check_upgrade` outside any section, and every other use of `mutations()` as they are after `serve-confirm-during-check`. If a call to settle verdicts still remains in the poll after that ticket, leave it where that ticket put it.
- `clutch/merge.py` `dirty_overlap`: take `ctx.git._commit_lock` inside `main_write()` around the status read, as `clutch/tickets.py` intake does.
- `docs/how-clutch-works.md` section 7.2 (the Dispatch bullet, the sentences on exclusive polls): the merge poll excludes the other exclusive sections but not running implementations and still marks serve busy; box intake with work, retro, the idle supervise pass, startup and sweeps still exclude slot-holding runs. Then `uv run clutch meta refresh docs/how-clutch-works.md`, changing nothing else in its header.
- Existing tests forced by the change: in `tests/unit/test_serve_idle_poll.py` the `owner` fixture gains a counting stand-in for `admission.merging` that appends `"merging"` and enters the real section, and `test_merge_work` expects `["merging"]` where it expects `["mutations", "exclusive"]` for the rows that have work (the idle rows stay `[]`); the box, scan and watch cases are unchanged. `tests/unit/test_merge_dirty.py` builds `git` as a `SimpleNamespace`, so `findings()` gains `_commit_lock=asyncio.Lock()`; its assertions are unchanged.
- New tests, each starting with a `clutch:meta` header from `uv run clutch meta refresh <file>` with only `purpose` edited by hand (if the serve lock blocks the refresh, the implementer creates the header): `tests/unit/test_admission_merging_section.py`, `tests/unit/test_merge_dirty_commit_lock.py`, `tests/integration/test_serve_merge_overlap.py` and the reproducer `tests/regress_serve_merge_off_exclusive.py`. Import `tests/integration/serve_rig.py` and change nothing in it. Follow the pattern of `tests/regress_serve_scan_watch_off_exclusive.py` for the reproducer.

Scope out: retro, the supervise pass, box intake, maintenance and startup keep `mutations()`/`exclusive()`; `Git.commit` lifts in `clutch/stages.py`; `clutch/git.py`, `clutch/scheduler.py`, `clutch/mergequeue.py`, `HOST_COMMAND_LOCK`; the design plans under `docs/`; `tests/integration/test_mergequeue.py`, `tests/integration/test_serve_parallel_admission.py` and `tests/integration/serve_rig.py` (no edits). If the implementer finds a merge-poll action that cannot be safe beside a run, keep that one action under `mutations()`, name it and the reason in the run record, and the criteria still hold for the common path.

## Scope fence
- clutch/daemon.py
- clutch/serve.py
- clutch/merge.py
- docs/how-clutch-works.md
- tests/unit/test_serve_idle_poll.py
- tests/unit/test_merge_dirty.py
- tests/unit/test_admission_merging_section.py
- tests/unit/test_merge_dirty_commit_lock.py
- tests/integration/test_serve_merge_overlap.py
- tests/regress_serve_merge_off_exclusive.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_admission_merging_section.py` uses a real `DaemonAdmission` (`max_runs` 2) with one run holding a slot: `merging()` is entered without waiting for that run; while its body is held `exclusive_pending()` is false and `_exclusive_waiters` is 0; a second `dispatch` is admitted and starts; `busy()` is true, `idle()` is false and `mutating` is the current task. The wrong results it rules out: `merging()` waiting for `_holding == 0`, or the second dispatch refused.
2. `./dev.py test tests/unit/test_admission_merging_section.py` also shows an `exclusive()` entered while a `merging()` body is held does not run its body until the merging body exits, and a `merging()` entered while an `exclusive()` body is held waits for it; both bodies never overlap. A cancelled merging body leaves `mutating` None and `busy()` false so a later `exclusive()` enters. The wrong result it rules out: overlapping bodies, or a flag left set after cancellation.
3. `./dev.py test tests/unit/test_serve_idle_poll.py` shows each `test_merge_work` row with work enters `merging` once and `mutations` and `exclusive` 0 times with one run holding a slot, each idle row enters none, and `test_idle_merge_detects_upgrade` still sets the upgrade flag with no entry. The wrong result it rules out: one entry into `mutations` or `exclusive`.
4. `./dev.py test tests/integration/test_serve_merge_overlap.py` runs serve through `tests/integration/serve_rig.py` with `max_runs` 2: ticket A is reviewed and queued for merge while ticket B's implementation is blocked on a release event. A's merged transition and squash commit on main are journaled while B is still blocked, `exclusive_pending()` is never true, and after B is released it rebases onto A's squash and merges with no tree-mismatch hold. The wrong result it rules out: A merging only after B is released.
5. `./dev.py test tests/unit/test_merge_dirty_commit_lock.py tests/unit/test_merge_dirty.py tests/unit/test_git_main_write.py` shows `dirty_overlap` does not call `status_porcelain` while another task holds the commit lock, and reads it after release; the findings tests pass; `test_git_main_write.py` passes unchanged. The wrong result it rules out: a status read taken with the commit lock held elsewhere.
6. `./dev.py test tests/integration/test_serve_upgrade.py tests/integration/test_serve_admission.py tests/integration/test_serve_parallel_admission.py tests/integration/test_sweep_slot_handoff.py tests/unit/test_admission_parallel_run_set.py tests/unit/test_admission_running_set.py tests/unit/test_daemon_admission_busy.py tests/unit/test_serve_scheduler_lifecycle.py` passes with none of those files edited, so handoff, stop, sweep and admission waits are preserved.
7. `uv run python tests/regress_serve_merge_off_exclusive.py` prints `{"regression_result": "pass"}` and exits 0 on the fixed branch, and prints `{"regression_result": "defect"}` with a non-zero exit on the merge base. It drives `Serve.merge` against a real `DaemonAdmission` (`max_runs` 2) with one run holding a slot and a queue whose `process` blocks on an event; it passes only when `process` is entered and a second dispatch starts before the held run is released.
8. `uv run clutch meta check tests/unit/test_admission_merging_section.py tests/unit/test_merge_dirty_commit_lock.py tests/integration/test_serve_merge_overlap.py tests/regress_serve_merge_off_exclusive.py docs/how-clutch-works.md` exits 0.

## Verification
```
./dev.py test tests/unit/test_admission_merging_section.py tests/unit/test_merge_dirty_commit_lock.py tests/integration/test_serve_merge_overlap.py tests/unit/test_serve_idle_poll.py tests/unit/test_merge_dirty.py tests/unit/test_git_main_write.py tests/integration/test_serve_upgrade.py tests/integration/test_serve_admission.py tests/integration/test_serve_parallel_admission.py tests/integration/test_sweep_slot_handoff.py tests/unit/test_admission_parallel_run_set.py tests/unit/test_admission_running_set.py tests/unit/test_daemon_admission_busy.py tests/unit/test_serve_scheduler_lifecycle.py
```

## Definition of rejected
The merge poll waiting for `_holding == 0` or counting as an exclusive waiter; the merge poll overlapping box intake, retro, the supervise pass or maintenance; serve idle, sweeping, handing off or stop-exiting while a merge poll runs; `dirty_overlap` reading status without the commit lock; a new lock type, a DuckDB state or a dual path beside `mutations()` for the merge poll; an edit to `clutch/git.py`, `clutch/scheduler.py`, `clutch/mergequeue.py`, `tests/integration/serve_rig.py` or `tests/integration/test_mergequeue.py`; the reproducer passing on the merge base.

## Time budget
- expected: 30m
- stuck: 60m
- reason: one small state bit in `DaemonAdmission`, a one-line call-site swap, one lock added to `dirty_overlap`, and one test file per layer; not split because the lock and its caller must land together

## Regression
```
uv run python tests/regress_serve_merge_off_exclusive.py
```
- carries: tests/regress_serve_merge_off_exclusive.py
