---
state: confirmed
source: human
priority: P0
kind: bug
---

## Depends on
- none

## Runs before
- serve-flaky-tests-deterministic

## Context
- clutch/serve.py::Serve.verdicts
- clutch/serve.py::Serve.maintenance
- clutch/daemon.py::DaemonCore.sweep_orphans
- clutch/restart.py::Restart.sweep_orphans
- clutch/reconcile.py::orphans
- clutch/reconcile.py::reconcile
- clutch/runner.py::apply_admission
- clutch/stages.py
- tests/integration/test_serve_confirm_during_check.py
- tests/integration/serve_rig.py
- tests/regress_serve_confirm_during_check.py

## Goal / Why
Since merge 99c9d7ec (`serve-confirm-during-check`, 2026-11-21), serve can journal `{"to": "abandoned"}` for a draft ticket while its confirmation is being applied. Before that merge, the merge consumer applied confirmations inside `admission.merging()`. That made `admission.busy()` true, so `Serve.maintenance` skipped the idle orphan sweep. The merge moved settlement to the new `Serve.verdicts` worker, which holds no admission boundary. `runner.apply_admission` journals ticket-keyed effect intents (`<request key>/baseline`, then the request key) and awaits git before completing them. `reconcile.orphans` counts any intent without a completion as an open run. So an idle sweep that reads the journal inside that window reaps the stem and journals `abandoned` with a `recovery_alert` whose reason is `orphaned run`.

Observed on 2026-11-22: Check of `serve-flaky-tests-deterministic` attempt 2 reran `tests/integration/test_host_loop.py`. All 3 tests errored because fixture member `merge-bonus` ended `abandoned` while the harness was confirming its draft (evidence file in `evidence/`). The same suite passed on the base commit and in the first candidate run. The implementer saw the same race and filed box-001062-cbf86391. The same window applies to an operator confirming a real draft while serve is idle.

After this ticket, the idle orphan sweep never reaps a stem while `Serve.verdicts` is settling admissions, and the confirmation completes and leaves the ticket confirmed, not abandoned. Orphans whose open run belongs to no live verdict, run or admission are still reaped exactly as today.

## Boundary contract
### Serve idle orphan sweep
- disposition: extend
- owner: clutch/serve.py
- consumers: `Serve.maintenance` through `DaemonCore.sweep_orphans` and `Restart.sweep_orphans`
- observable change: restores the pre-99c9d7ec guarantee that applying a verdict and the idle orphan sweep never overlap; while `Serve.verdicts` is inside `settle_admissions`, `Restart.owned()` is true, so the sweep returns `[]`
- compatibility: startup reconciliation, the drain and `clutch engine run` reconcile paths, and the reaping of real orphans are unchanged; confirm and reject request effects, keys and commits are unchanged; verdicts still apply while an unrelated run holds its slot
- acceptance: a sweep that runs while a confirmation's effect intent is open reaps nothing and the confirmation completes `confirmed`
- tests: the new integration test and regression reproducer named in Acceptance criteria, plus the existing `tests/integration/test_serve_confirm_during_check.py`
- post-merge source of truth: clutch/serve.py

## Scope in / Scope out
Scope in: in `clutch/serve.py`, mark the span in which `Serve.verdicts` awaits `self.control.inbox.settle_admissions(...)`. Extend the existing `self.core.restart.owned` lambda (set in `Serve.__init__`) so it is also true during that span. The flag is cleared in a `finally`, so a raising verdict cannot leave sweeps disabled. Add the new integration test, unit test and regression reproducer below.

The regression reproducer `tests/regress_reconcile_confirming_draft.py` is self-contained. The bug-evidence gate overlays only that one file onto the merge base, where `tests/integration/test_serve_verdict_orphan_sweep.py` and `tests/unit/test_serve_verdict_owned.py` do not exist. So the reproducer must not import or run either new test. It inlines the event-held confirmation scenario and its result check, and imports only modules present on the merge base: `clutch/*` (for example `clutch/serve.py`, `clutch/runner.py`, `clutch/reconcile.py`) and existing `tests/integration` helpers such as `tests/integration/serve_rig.py`. It follows the result protocol `clutch/stages.py` checks: on head it prints `{"regression_result": "pass"}` and exits 0. On the overlaid base it prints `{"regression_result": "defect"}` and exits 1 (a positive exit). On any setup failure it prints `error` and exits 2. The existing `tests/regress_serve_confirm_during_check.py` shows the protocol shape, but unlike that file this reproducer must not delegate to a test file that is new on the branch.

The `clutch/serve.py` fix, the integration test and the unit test from the previous attempt stay as they are; the Verification command passed with them. The ruff E501 in `tests/unit/test_driver_check_nesting.py` comes from the base run, is outside the fence, and is not edited.

Scope out: `clutch/reconcile.py`, `clutch/restart.py`, `clutch/daemon.py`, `clutch/runner.py` and `clutch/stages.py` stay unchanged, as do orphan semantics for startup and the drain. The flaky deadline work and the quarantine-cap finding on `test_live_keep_dispatches_again_without_restart` stay in `serve-flaky-tests-deterministic` and `serve-live-keep-single-verdict`. Do not add tests to `tests/integration/serve_rig.py`, `tests/integration/test_cli.py` or any other hot test file; importing their helpers is fine.

## Scope fence
- clutch/serve.py
- tests/integration/test_serve_verdict_orphan_sweep.py
- tests/unit/test_serve_verdict_owned.py
- tests/regress_reconcile_confirming_draft.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_serve_verdict_orphan_sweep.py` passes. It holds a confirmation of a draft stem open between its effect intent and completion with an `asyncio.Event` (no sleeps or wall-clock deadlines), runs `Serve.maintenance` once, then releases. It asserts that no `{"to": "abandoned"}` transition and no `orphaned run` recovery alert exist for the stem, and that the request's `ticket-plane/<stem>/confirm/<request>` effect completed. Without the fix the stem is `abandoned`.
2. `./dev.py test tests/unit/test_serve_verdict_owned.py` passes. With fakes, it asserts that the `Restart.owned` callable serve installs returns `True` while `settle_admissions` is awaited and `False` after it returns or raises, not `True` after a raising verdict.
3. `./dev.py test tests/integration/test_serve_confirm_during_check.py` still passes, so verdicts still apply while an unrelated Check holds its slot.
4. `uv run python tests/regress_reconcile_confirming_draft.py` prints `{"regression_result": "pass"}` and exits 0 on the branch. It decides deterministically with an inlined `asyncio.Event`-held confirmation window and one `Serve.maintenance` run, with no sleeps or deadlines, and imports no file that is absent from the merge base.
5. Proven before commit in a real merge-base git worktree with only `tests/regress_reconcile_confirming_draft.py` copied in: `uv run python tests/regress_reconcile_confirming_draft.py` prints `{"regression_result": "defect"}` and exits 1, because the stem ends `abandoned` with an `orphaned run` alert. Removing the fix by hand on the branch does not count as this proof.

## Verification
```
./dev.py test tests/integration/test_serve_verdict_orphan_sweep.py tests/unit/test_serve_verdict_owned.py tests/integration/test_serve_confirm_during_check.py
uv run python tests/regress_reconcile_confirming_draft.py
```

## Definition of rejected
- The fix suppresses the sweep for every stem permanently, or skips startup reconciliation.
- The fix changes `reconcile.orphans` to ignore admission-request intents. That would hide crash-orphaned confirmations from recovery.
- A test or the reproducer depends on sleeps, timeouts or load to hit the window.
- Confirmations again wait for unrelated run slots (`test_serve_confirm_during_check.py` fails).
- The reproducer imports or runs a file that exists only on the branch, so it cannot print `defect` on the overlaid base.

## Time budget
- expected: 15m
- stuck: 30m

## Regression
```
uv run python tests/regress_reconcile_confirming_draft.py
```
- carries: tests/regress_reconcile_confirming_draft.py