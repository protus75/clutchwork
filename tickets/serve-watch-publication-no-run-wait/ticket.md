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
- tests/unit/test_admission_parallel_run_set.py
- tests/integration/test_serve_parallel_admission.py
- tests/integration/serve_rig.py
- clutch/git.py
- clutch/tickets.py
- clutch/scheduler.py
- tickets/serve-watch-publication-no-run-wait/evidence/serve-watch-publication-waits.txt

## On-demand
- clutch/serve.py
- clutch/daemon.py
- docs/how-clutch-works.md

## Goal / Why
Every commit to main, including each ticket-plane commit an operator or the roadmap driver makes, makes serve's watcher wait for every running implementation and blocks admission of a ready ticket while it waits. `Serve.scan` takes `mutations()` (`admission.exclusive()`) whenever its intake snapshot changes, and the snapshot includes the sha of main and every ticket file, which every ticket-plane commit changes. `Serve.watch` then holds `admission.exclusive()` while it publishes the changed tickets. `exclusive()` waits until no run holds a slot and, while it waits, `_acquire_run` refuses new runs (`clutch/daemon.py`). With `scheduler.parallel` `max_runs` 2 and commits to main every few minutes, serve runs one implementation at a time for much of the time. The evidence file has the mechanism and the code lines.

After this ticket a commit to main made while an implementation runs never makes the watcher wait for that implementation and never blocks admission of a ready ticket. Intake still sees the new or changed ticket and publishes it to the scheduler, and intake's own commits still cannot overlap the merge queue's squash or delivery.

## Boundary contract
### Serve watcher intake and publication
- disposition: extend
- owner: clutch/serve.py (`scan`, `watch`) with `DaemonAdmission` in clutch/daemon.py
- consumers: ticket intake and publication for every new or edited ticket file, the scheduler's pending set, `clutch ticket review|confirm|reject` and the roadmap driver's commits, which reach the engine through it
- observable change: `scan` and `watch` take no section that waits for running implementations or counts as an exclusive waiter for admission; intake's commit and the scheduler publication each run under a lock that excludes only the writers that can race them (the merge queue's squash and delivery, and a dispatch selecting the next ticket)
- compatibility: the same intake commits, journal events, published ticket set and debounce behavior as today; `max_runs` 1 behaves as before; the merge queue, retro, upgrade and kill keep today's exclusion
- acceptance: criteria 1 to 6
- tests: tests/unit/test_serve_watch_no_wait.py and tests/integration/test_serve_watch_no_wait.py
- post-merge source of truth: clutch/serve.py and docs/how-clutch-works.md section 7.2

## Scope in / Scope out
Scope in:
- `clutch/serve.py` `scan` and `watch`: replace the two exclusive sections. The implementer reads `clutch/serve.py`, `clutch/daemon.py`, `clutch/git.py` and `clutch/tickets.py`, then lists in the run record every action the two sections perform and, for each, the writer it can race and the lock that now excludes it. The required invariants are:
  1. Intake's commits (`intake(...)` writing `clutch(<stem>): ticket` commits and stamping ticket files) hold `self.checkout.git.main_write()` (the lock that serializes merges into main) so they cannot overlap `merge_squash`, and keep using `Git.commit`'s `CommitLock`.
  2. Publication to the scheduler and the watcher (`self.core.watcher`, `self.core.scheduler.update`) cannot interleave with a dispatch selecting the next ticket: use the scheduler's own selection lock (`self._slot` in `clutch/scheduler.py`) or an equivalent that the scheduler already owns, not admission.
  3. Neither section waits for `_holding == 0` or increments `_exclusive_waiters`.
  4. A stop or kill request still stops the scan before it commits, as `if self.stopping: return {}` does today.
  If a site cannot be made safe without the exclusive section, keep that one site exclusive and name it and the reason in the run record; the criteria still apply to every other site.
- `clutch/daemon.py`: only if the change needs a small non-waiting gate in `DaemonAdmission`; say in the run record what and why.
- `docs/how-clutch-works.md` section 7.2: replace the sentence that says changed watch publication excludes running implementations: ticket intake and publication proceed beside running implementations; merge-queue processing and delivery still exclude them. After editing it, run `uv run clutch meta refresh docs/how-clutch-works.md` and change nothing else in its header.
- Existing tests that pin the exclusion change to the new contract: `tests/unit/test_admission_parallel_run_set.py::test_watch_publication_excludes_runs` and the scan and watch cases of `tests/unit/test_serve_idle_poll.py` (`test_scan_inputs_and_own_writes`, `test_pending_stem_state_retries_intake`, `test_watch_idle_skips_publication_gate`, `test_watch_changed_publication_enters_once`): each asserts what it asserts today about snapshots and debounce, and the entries into `mutations()` and `exclusive()` become 0. Nothing else in those files changes.
- New tests, each file starting with a `clutch:meta` header created by `uv run clutch meta refresh <file>` with only the `purpose` line edited by hand: `tests/unit/test_serve_watch_no_wait.py`, `tests/integration/test_serve_watch_no_wait.py` and the reproducer `tests/regress_serve_watch_no_wait.py` that `## Regression` names. Import `tests/integration/serve_rig.py` and change nothing in it.

Scope out: verdict settlement (`settle_admissions`, `apply_verdict`), which is the separate ticket `serve-verdicts-wait-for-runs`; the merge queue, retro, upgrade and kill handling; the box-intake poll; what intake does to a ticket; `clutch/runner.py`; `config.yaml`.

## Scope fence
- clutch/serve.py
- clutch/daemon.py
- docs/how-clutch-works.md
- tests/unit/test_admission_parallel_run_set.py
- tests/unit/test_serve_idle_poll.py
- tests/unit/test_serve_watch_no_wait.py
- tests/integration/test_serve_watch_no_wait.py
- tests/regress_serve_watch_no_wait.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_serve_watch_no_wait.py` runs serve through `tests/integration/serve_rig.py` with `max_runs` 2 and one implementation blocked on a release event. A ticket-plane commit to main made while it is blocked (a new draft ticket file committed, and a confirm of it) is intaken and published within 5 seconds of the fake clock, which the test advances past `SERVE_POLL_S` at least three times, before the blocked implementation is released, not after it ends.
2. The same test shows that, after the commit and the poll interval, a second ready ticket with a disjoint fence is admitted and starts while `one` is still held, so two implementations overlap, and that `admission.exclusive_pending` is never true during the wait.
3. The same test shows a change to a ticket file made while a run is held is published (the scheduler's pending set holds the new content) and a stop request published at the same time is still honored, not dropped. Check: `./dev.py test tests/integration/test_serve_watch_no_wait.py`.
4. `./dev.py test tests/unit/test_serve_watch_no_wait.py` shows the scan and watch bodies, run with a changed snapshot and one run holding a slot, enter the new intake lock and the scheduler lock and enter neither `mutations()` nor `admission.exclusive()` (counting stand-ins are entered 0 times, not once), that intake's commit is made while `main_write()` is held (a stand-in `main_write` lock records it), and that publication and a stand-in dispatch selection never interleave.
5. `./dev.py test tests/unit/test_serve_idle_poll.py tests/unit/test_admission_parallel_run_set.py tests/integration/test_serve_parallel_admission.py tests/integration/test_serve_admission.py` passes, with only the cases named in Scope in changed.
6. `uv run python tests/regress_serve_watch_no_wait.py` prints `{"regression_result": "pass"}` and exits 0 on the fixed branch and `{"regression_result": "defect"}` with a non-zero exit on the merge base, as `## Regression` states.
7. `uv run clutch meta check tests/unit/test_serve_watch_no_wait.py tests/integration/test_serve_watch_no_wait.py tests/regress_serve_watch_no_wait.py docs/how-clutch-works.md` exits 0 (only the files this ticket creates or edits).

## Verification
```
./dev.py test tests/integration/test_serve_watch_no_wait.py tests/unit/test_serve_watch_no_wait.py tests/unit/test_serve_idle_poll.py tests/unit/test_admission_parallel_run_set.py tests/integration/test_serve_parallel_admission.py tests/integration/test_serve_admission.py
```

## Definition of rejected
An intake commit that overlaps the merge queue's squash or delivery; a publication that interleaves with a dispatch selection; a stop or kill request dropped or delayed longer than today; merge processing, retro or upgrade handling allowed to overlap a running implementation; any change to what intake does to a ticket file; the regression reproducer passing on the merge base; a test or fixture added to `tests/integration/serve_rig.py` or another hot test file.

## Time budget
- expected: 30m
- stuck: 60m
- reason: two sections in one file, a lock chosen from locks the engine already has, one test per layer and one reproducer

## Regression
```
uv run python tests/regress_serve_watch_no_wait.py
```
- carries: tests/regress_serve_watch_no_wait.py
