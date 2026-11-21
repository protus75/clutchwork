---
state: draft
source: human
priority: P0
kind: bug
---

## Depends on
- serve-scan-watch-off-exclusive

## Context
- clutch/serve.py::Serve.merge
- clutch/serve.py::Serve.merge_work
- clutch/serve.py::Serve.apply_verdict
- clutch/serve.py::Serve.upgrade_idle
- clutch/serve.py::Serve.abort
- clutch/serve.py::Serve.__init__
- clutch/runner.py::apply_admission
- clutch/runner.py::verdict_locked
- clutch/runner.py::reject_ticket
- clutch/git.py::Git.commit_edit
- clutch/daemon.py::DaemonAdmission
- clutch/control.py::ControlInbox.settle_admissions
- tests/unit/test_serve_idle_poll.py
- tests/integration/test_serve_parallel_admission.py
- tests/regress_serve_parallel_admission.py
- tickets/serve-scan-watch-off-exclusive/ticket.md
- tickets/serve-verdicts-off-exclusive/evidence/serve-verdict-evidence.txt

## On-demand
- docs/how-clutch-works.md

## Goal / Why
A confirm or reject sent to a running `clutch engine serve` is applied only after every running implementation finishes, and while it waits the engine admits no new run. On 2026-11-21 a confirm submitted 10:58:51Z was applied at 11:05Z, when the one running ticket merged, and a second ready ticket with a disjoint fence never started; a later confirm of `requisition-review-input-reuse` (16:40Z) waited again. With `scheduler.parallel` `max_runs` 2 serve behaves like one run at a time (the owner's P0 complaint). The evidence file has the timeline and the code read.

Cause: the merge poll in `clutch/serve.py` (`Serve.merge`) takes one exclusive section (`self.mutations()`, which is `DaemonAdmission.exclusive()`) for two jobs, applying verdicts (`control.inbox.settle_admissions(self.apply_verdict)`) and processing the merge queue. `exclusive()` waits for `_holding == 0` and, while it waits, `_acquire_run` refuses new runs and `Serve.dispatch` skips `dispatch_next`. The earlier ticket `serve-verdicts-wait-for-runs` proposed a Serve-only repo lock and was rejected because engine writers then committed ticket files outside any shared lock. That is fixed: the merged chain `git-commit-edit-owner`, `runner-ticket-writes-commit-edit`, `rework-ticket-writes-commit-edit`, `author-ticket-writes-commit-edit` and `ticket-write-serialization-proof` makes every ticket-file stamp plus commit run inside one `Git.commit_edit` callback (`main_write()` then the commit lock), and intake takes the same two locks (`clutch/tickets.py` 966-967).

What each verdict path writes, from the code, and what it can race:
- `apply_admission` (`clutch/runner.py`) reads the journal, records a baseline `rev_parse HEAD` effect, may repair a replayed commit through `commit_edit`, reads `git log`, appends journal signals, then calls `verdict_locked`.
- `verdict_locked` first runs `intake(stems={stem})` (both locks). Confirm of a draft stamps `state: confirmed` and commits inside `commit_edit`, re-checking the draft state inside the callback, then journals `draft_confirmed`. Reject goes through `reject_ticket`: a `commit_edit` stamp-and-commit, then journal signals and `_dead_dependents`, which only enqueues a Box message and appends a journal signal (synchronous, no repo write). A confirm of a Reject-queue stem journals `reject_verdict keep` and writes no file.
- Every write to `tickets/<stem>/ticket.md` is therefore atomic against intake, `merge_squash` (also `main_write()` then the commit lock), the other `commit_edit` writers and the roadmap driver, which already runs beside runs and takes `main_write()`. The remaining plain `Git.commit` writers (`lift_outbox`, prior-diff in `clutch/stages.py`) write run-record paths, never `ticket.md`, and the commit lock serializes the index. Journal and Box writes are synchronous in one event loop.
- Verdicts and the merge queue never need a lock between them: both run in the one `merge` consumer task, so settling verdicts first and then taking `mutations()` for the queue keeps them sequential, exactly as today's single section does.
- `settle_admissions` handles only `confirm` and `reject`; box triage (`settle_triage`) runs from `Serve.dispatch` supervise under `mutations()` and stays there.

One race the exclusion hid and this ticket must close. Today no run can start while a verdict is applied. Beside running work, `verdict_locked` reads the journal state ("is running" refusal) before `commit_edit`, and `Serve.__init__`'s `dispatch` reads `main:<ticket>` (`rev_parse`, then `git show`) and later `mark_running` with no lock. A reject of a confirmed, queued ticket can therefore pass its refusal check, then the ticket starts, then the reject commits `state: rejected` onto a ticket that is running, or the reject commits between dispatch's two reads and the rejected ticket still starts. A confirm cannot race a start (a draft is never dispatched), and a Reject-queue stem is held.

Self-upgrade and kill: `upgrade_idle()` is true while only `admission.mutating` is checked, and `abort()` cancels `admission.mutating` and the run tasks before `WorkerStop` cancels workers. A verdict settled outside `mutations()` would be invisible to both, so a handoff re-exec or `WorkerStop` could cancel it mid git subprocess (a killed `git commit` can leave `index.lock`). Registering it is required; it is a marker on Serve, not a lock.

After this ticket a confirm or reject is applied without waiting for running implementations and without being an exclusive waiter, a second ready ticket is admitted meanwhile, and a verdict never lands on a ticket that has started.

## Boundary contract
### Serve verdict settlement
- disposition: extend
- owner: clutch/serve.py (`merge`, `merge_work`, `upgrade_idle`, `abort`, the dispatch closure in `__init__`) and clutch/runner.py (`reject_ticket`)
- consumers: `clutch ticket confirm` and `clutch ticket reject` requests published to a running serve, the VS Code extension's confirm and reject actions, self-upgrade handoff, stop and kill
- observable change: accepted confirm and reject requests are settled by the merge consumer before its queue section, outside `mutations()`, so they neither wait for running implementations nor count as an exclusive waiter. `merge_work()` loses its two verdict cases and a new `verdict_work()` holds them. An in-flight settlement is registered on Serve (`settling`) so `upgrade_idle()` is false and `abort()` cancels and observes it. Dispatch's ticket read and `mark_running` run under `git.main_write()`. `reject_ticket`'s `commit_edit` callback refuses with the "is running" refusal if the journal now says running.
- compatibility: same ticket-plane commits, journal signals, `verdict_refused` events and request effects as today, applied in the same order and still before the queue's processing in the same consumer task; merge-queue processing and delivery, stop and kill requests, retro, supervise and triage, box intake, maintenance, upgrade and startup keep their exclusion; `max_runs` 1 behaves as before; the engine's own `reject_ticket` call after a terminal transition is unchanged
- acceptance: criteria 1 to 7
- tests: tests/unit/test_serve_verdict_settle.py and tests/integration/test_serve_verdict_overlap.py
- post-merge source of truth: clutch/serve.py and docs/how-clutch-works.md section 7.2

### Admission exclusion and locks
- disposition: reuse
- owner: clutch/daemon.py::DaemonAdmission and clutch/git.py::Git.main_write
- consumers: merge queue, retro, supervise, box intake, maintenance, startup
- observable change: none; `exclusive()`, `mutations()`, `main_write()` and the commit lock are unchanged and no lock type is added
- compatibility: every other caller keeps today's exclusion
- acceptance: criterion 7
- tests: tests/unit/test_serve_idle_poll.py
- post-merge source of truth: clutch/daemon.py::DaemonAdmission

## Scope in / Scope out
Scope in:
- `clutch/serve.py` `merge`: `poll()` calls `check_upgrade` as today, then `if self.verdict_work(): await self.settle_verdicts()`, then `if not self.merge_work(): return` and the existing `mutations()` body minus `settle_admissions` (its `control.poll()`, `stopping`/kill return, `queue is None` return, `process()`, delivery and writer pruning are unchanged). `settle_verdicts()` does `self.control.poll()`, returns if `self.stopping` or a kill is requested, sets `self.settling = asyncio.current_task()`, awaits `self.control.inbox.settle_admissions(self.apply_verdict)` and clears `settling` in a `finally`. `Serve.__init__` sets `self.settling = None`; no `getattr` fallback.
- `clutch/serve.py` `verdict_work()` returns True for exactly the two cases `merge_work()` loses (an accepted `confirm` or `reject` decision with no `hold_id` whose `ticket-plane/<stem>/<verb>/<request_id>` effect is not completed, and an undecided inbox request file, including the `OSError` branch); the stop, kill and queue cases stay in `merge_work()`, so a stop or kill request still takes `mutations()` exactly as today.
- `clutch/serve.py` `upgrade_idle()` also requires `self.settling is None`; `abort()` adds `self.settling` (when not None) to `operations`.
- `clutch/serve.py` dispatch closure in `__init__`: wrap the span from `rev_parse(main:<ticket>)` through `runner.mark_running` in `async with local.git.main_write():`; `await callback(ticket)` and the `finally` stay outside. Nothing inside takes a lock-taking Git writer (it only reads Git and appends to the journal). `local.git` is the same `Git` object as `self.checkout.git` (the prepared checkout is `dataclasses.replace` of it); the implementer confirms this in the run record.
- `clutch/runner.py` `reject_ticket`: inside `reject_edit` (the `commit_edit` callback), after the existing state check, `if refusal := verdict_refusal(admission_facts(checkout.journal.read()), stem, True, False, set()): raise Refusal(*refusal)`. `apply_admission` already turns a `Refusal` into the verdict's refusal. The call after a terminal transition (`runner.py` ~519) has a terminal state and is unaffected; the implementer states this in the run record.
- `docs/how-clutch-works.md` section 7.2 Dispatch bullet: change "A poll with work excludes running implementations until it finishes; an idle poll takes no exclusive section" to say a verdict is applied beside running implementations, while merge-queue processing and delivery, stop and kill, retro, supervise and maintenance still exclude them. Then `uv run clutch meta refresh docs/how-clutch-works.md`, changing nothing else in its header. The sibling `serve-scan-watch-off-exclusive` edits the neighbouring sentence; read its merged text first and edit only what it left false.
- `tests/unit/test_serve_idle_poll.py`: in `test_merge_work` the rows `decision` and `inbox` now expect `owner.entries == []` (a verdict-only poll enters neither `mutations()` nor `exclusive()`) and also assert `settle_admissions` was awaited once; the rows `stop`, `kill` and every queue row keep today's expectation. The `owner` fixture gains `s.settling = None` and nothing else of its own (the sibling's fixture changes are already merged). Nothing else there changes.
- `tests/integration/test_serve_parallel_admission.py`: only `test_dispatch_consumed_confirm_and_stop` changes: after the confirm is consumed it is applied while `one` is still held (no wait for `exclusive_pending`; the `"state: draft"` assertion becomes `"state: confirmed"`), and a stop published before `one` is released still keeps `two` from running; nothing else in the file changes.
- New tests, each file starting with a `clutch:meta` header from `uv run clutch meta refresh <file>` with only `purpose` edited by hand (if the serve lock blocks the refresh, the implementer creates the header): `tests/unit/test_serve_verdict_settle.py`, `tests/integration/test_serve_verdict_overlap.py` and the reproducer `tests/regress_serve_verdicts_off_exclusive.py`. Import `tests/integration/serve_rig.py` and change nothing in it.
Scope out: box triage and `settle_triage`; the merge queue, `fill_slots`, `max_unmerged`; `clutch/daemon.py`, `clutch/git.py`, `clutch/control.py`, `clutch/scheduler.py`, `clutch/tickets.py`; any change to what a verdict commits or journals; `Serve.scan` and `Serve.watch` (the sibling ticket); `config.yaml`; `tests/regress_serve_parallel_admission.py` (scan only, unchanged by this ticket).

## Scope fence
- clutch/serve.py
- clutch/runner.py
- docs/how-clutch-works.md
- tests/unit/test_serve_idle_poll.py
- tests/integration/test_serve_parallel_admission.py
- tests/unit/test_serve_verdict_settle.py
- tests/integration/test_serve_verdict_overlap.py
- tests/regress_serve_verdicts_off_exclusive.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_serve_verdict_settle.py` shows that with one admission slot held (`_holding` 1) a verdict-only `merge` poll awaits `settle_admissions` and enters `mutations()` and `exclusive()` 0 times, not once, and that a poll with a stop or kill request still enters `mutations()` once.
2. `./dev.py test tests/unit/test_serve_verdict_settle.py` shows verdict settlement and queue processing never overlap: with `queue.process()` blocked, a verdict that arrives is not applied until the poll returns and is applied before the next `process()`, and settlement runs before `process()` within a poll that has both; the wrong result is two overlapping awaits.
3. `./dev.py test tests/unit/test_serve_verdict_settle.py` shows `upgrade_idle()` is false while a settlement is in flight and true after it finishes or raises, and `abort()` cancels and awaits the settling task; the wrong result is `upgrade_idle()` true mid-settlement.
4. `./dev.py test tests/unit/test_serve_verdict_settle.py` shows `reject_ticket` refuses with the "is running" refusal when the journal's last state for the stem is `running` at the time the `commit_edit` callback runs: the ticket bytes are unchanged and no `rejected` signal is journaled; the wrong result is a `state: rejected` stamp on a running ticket.
5. `./dev.py test tests/integration/test_serve_verdict_overlap.py` runs serve through `tests/integration/serve_rig.py` with `max_runs` 2 and one implementation blocked on a release event. A confirm for a draft published while it is blocked is applied (the `clutch(<stem>): confirmed` commit exists and `draft_confirmed` is journaled) before the release, within 5 seconds of the fake clock past `SERVE_POLL_S`, `admission.exclusive_pending()` is never true, and a second ready ticket with a disjoint fence starts so two implementations overlap; the wrong result is the second starting only after the first ends.
6. `./dev.py test tests/integration/test_serve_verdict_overlap.py` also shows a reject of a queued confirmed ticket applied during the blocked run, a refused verdict (a stem that is neither a draft nor in the Reject queue) journaling `verdict_refused` with today's reason, a stop request published meanwhile still honored, and, with the test holding `git.main_write()`, a ready ticket's dispatch journaling no `running` transition until the lock is released.
7. `./dev.py test tests/unit/test_serve_idle_poll.py tests/integration/test_serve_parallel_admission.py tests/integration/test_serve_admission.py tests/integration/test_serve_upgrade.py tests/unit/test_admission_parallel_run_set.py tests/unit/test_reject_reason_paths.py tests/integration/test_control_cli.py` passes, with only the rows and fixture field named in Scope in changed in `tests/unit/test_serve_idle_poll.py` and only `test_dispatch_consumed_confirm_and_stop` changed in `tests/integration/test_serve_parallel_admission.py`; the merge, box, retro and stop cases still enter `mutations()`.
8. `uv run python tests/regress_serve_verdicts_off_exclusive.py` prints `{"regression_result": "pass"}` and exits 0 on the fixed branch and `{"regression_result": "defect"}` with a non-zero exit on the merge base, as `## Regression` states.
9. `uv run clutch meta check tests/unit/test_serve_verdict_settle.py tests/integration/test_serve_verdict_overlap.py tests/regress_serve_verdicts_off_exclusive.py docs/how-clutch-works.md` exits 0.

## Verification
```
./dev.py test tests/unit/test_serve_verdict_settle.py tests/integration/test_serve_verdict_overlap.py tests/unit/test_serve_idle_poll.py tests/integration/test_serve_parallel_admission.py tests/integration/test_serve_admission.py tests/integration/test_serve_upgrade.py tests/unit/test_admission_parallel_run_set.py tests/unit/test_reject_reason_paths.py tests/integration/test_control_cli.py
```

## Definition of rejected
A verdict applied while the merge queue processes or delivers; a reject committed onto a ticket that has started, or a rejected ticket started; a new lock type, a DuckDB state or a dual path beside the old exclusive section; a verdict outside `upgrade_idle()` and `abort()`; a confirm or reject that commits or journals something different from today, in a different order, or loses a `verdict_refused`; a stop or kill request dropped or delayed longer than today; merge processing, retro, supervise, triage or maintenance moved off exclusion; `commit_edit` nested inside `main_write()` (deadlock); the reproducer passing on the merge base; an edit to `tests/integration/serve_rig.py` or another hot test file.

## Time budget
- expected: 30m
- stuck: 60m
- reason: one cause in one poll; the settlement move, a marker, one lock wrap in dispatch and one refusal re-check, with one test file per layer and one reproducer

## Regression
```
uv run python tests/regress_serve_verdicts_off_exclusive.py
```
- carries: tests/regress_serve_verdicts_off_exclusive.py
