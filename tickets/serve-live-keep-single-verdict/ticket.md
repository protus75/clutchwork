---
state: draft
source: human
priority: P0
kind: bug
---

## Depends on
- none

## Context
- clutch/runner.py::verdict_locked
- clutch/runner.py::apply_admission
- clutch/drain.py::record_reoffer
- clutch/status.py::reject_queue
- tests/integration/test_serve_dispatch.py::test_live_keep_dispatches_again_without_restart
- tests/integration/test_serve_dispatch.py::test_serve_reoffers_failed_dispatch_with_machine_keep_and_retry
- tests/integration/serve_rig.py::graph
- tests/integration/serve_rig.py::script
- tests/regress_lint_carries.py

## Goal / Why
`tests/integration/test_serve_dispatch.py::test_live_keep_dispatches_again_without_restart` fails under load with two `reject_verdict` keep signals instead of one (evidence file). The test's premise is right and the production code is wrong: this is a time-of-check to time-of-use race in `clutch/runner.py::verdict_locked`, not a test race.

Mechanism, with the failing run's journal in `evidence/`: a ticket parked in the Reject queue with an unspent retry cap is re-offered by serve itself (`clutch/serve.py` dispatch at line 161-164 calls `clutch/drain.py::record_reoffer` at line 106-109, which journals a `machine` keep and a `retry` draw, then `running`). An operator `confirm` request races it. `verdict_locked` reads the journal at `clutch/runner.py:707`, decides at line 713 that the stem is not running (`verdict_refusal` refuses a running stem with "is running", `clutch/status.py:185`), then awaits `git.rev_parse` at line 732. During that await serve's dispatch runs, journals the machine keep and `running`, and `verdict_locked` then appends an `operator` keep at line 745 from the stale snapshot. The failing journal shows exactly that order: `machine` keep, `cap_consumed retry`, `running`, then the `operator` keep. Effect in production, not only in the test: one re-offer is released twice, and the late operator keep opens a new lineage window (`clutch/caps.py::lineage` restarts counting at an operator keep), so the retry draw the machine just took is forgotten while the ticket runs. The machine side is not racy: `record_reoffer` appends its keep only while the stem is still in `reject_queue`, and it reads the journal after its own awaits (`clutch/serve.py:161`).

Fix, smallest: in `verdict_locked`, after the `await` at line 732 and before the `prior_keep` check, re-read `history` and recompute `refusal` with `verdict_refusal(admission_facts(history), stem, kill, draft, set())`, so the existing `if refusal: raise Refusal(...)` at line 743 sees a stem that serve already re-dispatched; no `await` may sit between that re-read and the append at line 745. A refused operator keep for a stem that is already running again is the designed outcome ("wait for its terminal, then retry"); `apply_admission` returns the refusal and serve logs `verdict_refused`. The original test then sees exactly one keep in either order (operator first: one operator keep; serve first: one machine keep and a refused operator request), so it needs no edit.

Rejected simpler approaches: counting only `actor == "operator"` keeps in the test (hides that the operator keep is applied to a running stem); holding serve's selection in the test (leaves the production race and the reset caps). A lock around admission and dispatch is larger than the re-read and would touch the scheduler.

Class prevention, named: the deterministic test below pins the interleaving through the `rev_parse` await, so a later reorder that reopens the window turns Check red. A broader audit for other read-await-append sequences in `clutch/runner.py` is not cheap or certain: `clutch box suggest`, not this diff.

Companion ticket `serve-flaky-tests-deterministic` fixes the wall-clock waits in the other two flaky groups; it is independent.

## Boundary contract
### Operator keep admission
- disposition: extend
- owner: clutch/runner.py
- consumers: `clutch/serve.py::Serve.apply_verdict` through `apply_admission`, `clutch/drain.py` drain admission, and the `confirm` verbs
- observable change: an operator `confirm` for a Reject-queue stem that serve re-dispatched while the verdict awaited git is refused with "is running" and journals no keep; every other path is unchanged
- compatibility: restores the existing "refuse a running stem" contract of `verdict_refusal`; no journal event shape, signal name or refusal text changes
- acceptance: the carried race test journals exactly one `reject_verdict` keep when the machine re-offer lands during the operator's `rev_parse`
- tests: tests/unit/test_runner_verdict_reread.py and the existing tests/integration/test_serve_dispatch.py cases
- post-merge source of truth: clutch/runner.py

## Scope in / Scope out
In: the re-read and recompute in `clutch/runner.py::verdict_locked` described above, a new test `tests/unit/test_runner_verdict_reread.py`, and a new reproducer `tests/regress_serve_live_keep.py`.

The new unit test drives `runner.verdict_locked` directly with fakes, no process or real git: a `tmp_path` repo holding a committed-looking `tickets/work/ticket.md` with `state: confirmed`; a real `Journal` under `tmp_path` seeded with a `running` transition and a `gate_failed` transition carrying `routed: reject_queue` and `dispatch: reject_queue` (the stem is in the Reject queue with its retry cap unspent); `runner.intake` monkeypatched to an async stub returning an object whose `refused` is `{}`; and a checkout stand-in (`SimpleNamespace` with `repo`, `journal`, `git`, `fs`, `config`) whose `git.rev_parse` is an async function that, on the call with argument `HEAD:tickets/work/ticket.md` (the call at `clutch/runner.py:732`), first runs `record_reoffer(journal, journal.read(), "work", sha)` and `runner.mark_running(journal, "work", sha)` (exactly what serve's dispatch does) and then returns a fixed sha. It awaits `verdict_locked("work", checkout, kill=False)` and asserts: it raises `Refusal` whose message contains "is running"; the stem's journal has exactly one `reject_verdict` keep and its `actor` is `machine`; no `operator` keep exists. No real time or load is involved. A second case in the same file leaves `rev_parse` plain and asserts the operator keep is journaled once and `verdict_locked` returns `EXIT_MERGED`, so the re-read does not refuse a stem that is still in the queue.

The reproducer `tests/regress_serve_live_keep.py` runs that test file in a subprocess (`sys.executable -m pytest -q -p no:cacheprovider -n0 tests/unit/test_runner_verdict_reread.py`, capturing its output) and prints one JSON object: `pass` on exit 0, `defect` on exit 1 (an assertion failed), `error` for any other exit code or a failure to start. Model the JSON and error handling on `tests/regress_lint_carries.py`.

Out: `tests/integration/test_serve_dispatch.py` (unchanged), `clutch/serve.py`, `clutch/drain.py`, the scheduler, locking, and any skip, xfail or retry loop.

## Scope fence
- clutch/runner.py
- tests/unit/test_runner_verdict_reread.py
- tests/regress_serve_live_keep.py

## Acceptance criteria
1. `uv run python tests/regress_serve_live_keep.py` prints `{"regression_result": "pass"}`, not `defect`: with the machine re-offer forced into the operator's `rev_parse` await, the journal holds one `reject_verdict` keep (actor `machine`), not two.
2. `./dev.py test tests/unit/test_runner_verdict_reread.py` passes and asserts `verdict_locked` raises `Refusal` containing "is running", not journals an operator keep, and that its second case still journals exactly one operator keep and returns `EXIT_MERGED`.
3. `./dev.py test tests/integration/test_serve_dispatch.py` passes, including `test_live_keep_dispatches_again_without_restart` unchanged, so an operator keep with no competing re-offer still journals exactly one keep.
4. `./dev.py test tests/unit tests/integration/test_serve_admission.py tests/integration/test_control_cli.py tests/integration/test_stale_running.py` passes, so refusal text and verdict ordering for the other `confirm` and `reject` paths are unchanged.

## Verification
```
uv run python tests/regress_serve_live_keep.py
./dev.py test tests/unit/test_runner_verdict_reread.py tests/integration/test_serve_dispatch.py tests/integration/test_serve_admission.py tests/integration/test_control_cli.py tests/integration/test_stale_running.py
```

## Definition of rejected
Reject the branch if it edits `tests/integration/test_serve_dispatch.py` to filter by actor or count differently, adds a skip, xfail or retry loop, adds an `await` between the re-read and the keep append, changes the refusal text, or changes any file outside the fence.

## Time budget
- expected: 15m
- stuck: 30m

## Regression
```
uv run python tests/regress_serve_live_keep.py
```
- carries: tests/regress_serve_live_keep.py
- carries: tests/unit/test_runner_verdict_reread.py
