---
state: draft
source: human
priority: P0
kind: feature
---

## Depends on
- main-checkout-write-gate

## Context
- clutch/drain.py::_Drain.run
- clutch/drain.py::_Drain._run_driver
- clutch/drain.py::_Drain._await_controlled
- clutch/drain.py::_Drain._between_tickets
- clutch/runner.py::bind
- clutch/runner.py::drive
- clutch/stages.py::StageContext
- tests/unit/test_driver_hooks.py
- tests/integration/test_roadmap_driver.py::test_drain_calls_driver_at_start_and_after_each_settle

## On-demand
- tests/unit/test_supervise_idle_hooks.py
- docs/how-clutch-works.md

## Goal / Why
In `clutch engine drain` the roadmap driver pass (Author and requisition-review LLM calls, roadmap row commits, `ship`, digest) runs as a background task that overlaps the next ticket run, so a confirmed eligible ticket is dispatched without waiting for the pass. Today `_Drain.run` awaits `_run_driver()` after every settle before it selects the next ticket. On 2026-11-19 `graphics-kind` was authored and requisition-reviewed by the driver while the confirmed tickets `document-agent-roadmap-prompt`, `graphics-kind` and `conflict-rerun-accounting` waited; the owner requires authoring to overlap implementation. Main-checkout writes stay serialized: `main-checkout-write-gate` makes the driver's row commits, ticket commits, decision-record commits and `ship` hold `Checkout.main_writes`; this ticket makes drain's intake and its inline merge admission hold the same lock, so a driver write never lands between a merge's rebase and its squash or between an Author ticket write and its commit.

## Boundary contract
### Drain driver scheduling
- disposition: extend
- owner: clutch/drain.py
- consumers: `clutch engine drain` (composed in clutch/__main__.py with `_driver = build_driver()`), docs/how-clutch-works.md sections 7.1 and 7.5
- observable change: `_run_driver` starts `self.driver_task = asyncio.create_task(self.driver(self.c, log))` and returns at once instead of awaiting the pass. `_Drain` gains class attribute `driver_task = None`. The start condition is today's (driver set, `docs/roadmap.md` present, `_between_tickets()`, settle count differs from `driven`) plus `self.driver_task is None`; `driven` is set when the task starts, as today. At the top of each loop iteration a finished `driver_task` is cleared and its `result()` re-raises, so a driver error still stops the drain. The Suggestion Box triage and `supervise_idle` block runs only while `driver_task is None` (the driver's own triage pass and the idle one never run at once). When `_select` picks nothing and `driver_task` is pending, `run` awaits it under `_await_controlled` (with a no-op abort, as `_run_driver` does today) and re-loops instead of settling, because the pass may have authored work. `run` never returns while `driver_task` is pending: when `_stopping()` (kill) holds it cancels the task and awaits its cancellation; on stop, deadline halt or self-upgrade it awaits the task under `_await_controlled`
- compatibility: the driver still runs at start and after every settle, once per settle count, with the same arguments; retro ordering, retry-cycle grouping and the stop/kill/handoff contract are unchanged; a drain with no `docs/roadmap.md` or no driver behaves exactly as before
- acceptance: a confirmed ticket's `_run_one` starts while a blocked driver task is still pending
- tests: tests/unit/test_drain_driver_overlap.py, tests/unit/test_driver_hooks.py, tests/unit/test_supervise_idle_hooks.py, tests/integration/test_roadmap_driver.py
- post-merge source of truth: clutch/drain.py::_Drain.run

### Drain main-checkout write gate holders
- disposition: extend
- owner: clutch/drain.py, clutch/runner.py, clutch/stages.py
- consumers: drain's intake, `runner.drive` inline merge (drain and `engine run`), the driver writers from `main-checkout-write-gate`
- observable change: the `intake(...)` call at the top of the `_Drain.run` loop runs inside `async with self.c.main_writes:`. `StageContext` gains `main_writes: asyncio.Lock = field(default_factory=asyncio.Lock, compare=False, repr=False)`; `runner.bind` constructs its `StageContext` with `main_writes=checkout.main_writes`; in `runner.drive` the inline `merge(ctx, ticket, attempt=run.attempt)` call (the branch where `admission is None`) runs inside `async with ctx.main_writes:`. The `admission(...)` branch serve uses is unchanged here
- compatibility: merge results, intake results and journal events are unchanged; every existing `StageContext(...)` construction stays valid
- acceptance: intake and the inline merge each observe their lock held, and `bind(checkout, llm)` hands its stages the checkout's lock object
- tests: tests/unit/test_drain_driver_overlap.py
- post-merge source of truth: clutch/drain.py, clutch/runner.py::drive, clutch/stages.py::StageContext

## Scope in / Scope out
Scope in:
- `clutch/drain.py`: the scheduling and intake changes declared above; nothing else in drain.py changes.
- `clutch/stages.py`: add the `main_writes` field to `StageContext` (import `field` if needed); nothing else.
- `clutch/runner.py`: pass `main_writes=checkout.main_writes` in `bind`'s `StageContext(...)`, and hold `ctx.main_writes` around the inline `merge(...)` call in `drive`; nothing else.
- `tests/unit/test_driver_hooks.py::test_drain_runs_driver_between_tickets`: add `main_writes=asyncio.Lock()` to its `SimpleNamespace` checkout; its assertions stay (the driver is still awaited once per settle count before `run` returns).
- `tests/unit/test_supervise_idle_hooks.py`: add a `main_writes` lock to the checkout fake `drain_rig` callers pass, if the drain tests there fail without it; `test_drain_boundary_order` keeps its expected order `["retro", "driver", "supervise"]` (it mocks `_run_driver`, which still runs before the triage block); change nothing else.
- `tests/integration/test_roadmap_driver.py::test_drain_calls_driver_at_start_and_after_each_settle`: the one expectation that may change is the `script.calls` snapshot inside each recorded tuple, which may now include the ticket dispatched concurrently with the pass; keep the asserted settle counts `[0, 1, 2]` and last-merged stems `[None, "one", "two"]` exactly, and keep `[]` when the roadmap is absent.
- `docs/how-clutch-works.md`: in section 7.1 step 2, say the roadmap driver starts after a settle and runs alongside the next ticket, and that the drain waits for an in-flight pass before settling or exiting; in section 7.5 first paragraph, add one sentence that the pass overlaps ticket runs and that its main-checkout writes (row and ticket commits, decision records, `ship`) hold one lock with intake and merge admission.
- New `tests/unit/test_drain_driver_overlap.py` covering each acceptance criterion with fakes and `tmp_path` only.

Scope out: serve (`serve-driver-overlaps-dispatch`), the gate's driver-side holders (`main-checkout-write-gate`), `roadmap.drive` and `build_driver`, the retro scheduling, and `tests/integration/test_drain.py` (no assertion there depends on driver ordering; do not add tests to it).

## Scope fence
- clutch/drain.py
- clutch/runner.py
- clutch/stages.py
- tests/unit/test_drain_driver_overlap.py
- tests/unit/test_driver_hooks.py
- tests/unit/test_supervise_idle_hooks.py
- tests/integration/test_roadmap_driver.py
- docs/how-clutch-works.md

## Acceptance criteria
1. `tests/unit/test_drain_driver_overlap.py` runs `_Drain.run` with a driver that blocks on an `asyncio.Event` and a `_select` that offers one confirmed ticket, and asserts `_run_one` was awaited while the driver task was still pending (wrong result: `_run_one` starts only after the driver returns); checked by `./dev.py test tests/unit/test_drain_driver_overlap.py`.
2. The same file asserts that when `_select` picks nothing and the driver task is pending, `_settle` is called only after the driver finished (recorded order `["driver_done", "settle"]`, not `["settle", ...]`), and that `run` does not return before then.
3. The same file asserts a driver raising `RuntimeError("boom")` makes `run` raise `RuntimeError` with `boom`, not return a report.
4. The same file asserts that with `_stopping()` true after a dispatch, `run` returns with the driver task `cancelled()` and not pending.
5. The same file asserts the Suggestion Box triage and `supervise_idle` are not called while a driver task is pending, and are called once it has finished.
6. The same file asserts the drain's `intake` call observes `c.main_writes.locked()` as `True`; that `runner.drive` with `admission=None` calls a monkeypatched `runner.merge` while `ctx.main_writes.locked()` is `True`; and that the `StageContext` `runner.bind(checkout, llm)` builds has `main_writes is checkout.main_writes`.
7. The existing ordering tests still pass with only the edits Scope in names: `./dev.py test tests/unit/test_driver_hooks.py tests/unit/test_supervise_idle_hooks.py tests/integration/test_roadmap_driver.py`.

## Verification
```
./dev.py test tests/unit/test_drain_driver_overlap.py tests/unit/test_driver_hooks.py tests/unit/test_supervise_idle_hooks.py tests/integration/test_roadmap_driver.py
./dev.py test
```

## Definition of rejected
`_Drain.run` still awaits a whole driver pass before selecting the next ticket; two driver passes run at once; `run` can return or hand off while a driver task is pending; a driver error is swallowed; drain's intake or inline merge runs without holding `main_writes`; serve code changes; or a test is added to `tests/integration/test_drain.py`.

## Time budget
- expected: 25m
- stuck: 50m
