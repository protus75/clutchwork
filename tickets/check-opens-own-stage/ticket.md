---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- none

## Runs before
- supervisor-orders-by-depends

## Context
- clutch/stages.py::check
- clutch/stages.py::check_meta
- clutch/stages.py::run_stages
- clutch/driver.py::Driver.stage
- clutch/metafill.py
- clutch/llm.py::FakeLLM
- tests/integration/test_host_mechanical.py
- tests/unit/test_check_meta_fill.py
- docs/how-clutch-works.md#5. Checks

## Goal / Why
On 2026-11-22 `engine serve` stopped with `stage already open: stem=serve-flaky-tests-deterministic, surface=check` (see `check-meta-fill-nested-stage`, which fixes that instance). `check-owns-meta-headers` had added a model call (`metafill.make_ask`, surface `meta`) inside Check, and nothing in the test suite ran it inside an open `check` stage:

- `run_stages` opens `Driver.stage(surface="check")` around the call to `stages.check`. Every Check test calls `stages.check` directly, so none of them runs inside the nesting guard in `Driver.stage`.
- No integration test sets `meta.paths`, so `check_meta` never ran its model branch through a real `Driver`. `tests/unit/test_check_meta_fill.py` replaces the driver with a stub and `make_ask` with a mock.

Any future model call added inside Check would merge the same way and stop serve on its first real run. After this ticket, `stages.check` opens its own `check` stage, so every existing Check test exercises the real nesting guard. One integration test also runs Check with `meta.paths` set, an edited file under that path, and a real `Driver` with `FakeLLM`.

## Boundary contract
### Check stage events
- disposition: extend
- owner: clutch/stages.py
- consumers: run_stages, engine.log readers (observe, status), every test that calls stages.check
- observable change: the `check` `stage_start`/`stage_end` pair is emitted by `stages.check` itself, so a direct caller of `stages.check` gets the events and the open-stage guard; `run_stages` no longer opens the check stage
- compatibility: for pipeline runs, the engine.log sequence (one `stage_start` then one `stage_end` with the result's outcome for each Check) is unchanged; `review_visual` and the `meta` fill still nest under it
- acceptance: criteria 1 to 4
- tests: tests/unit/test_check_stage_events.py, tests/integration/test_check_meta_fill_stage.py
- post-merge source of truth: clutch/stages.py

## Scope in / Scope out
Scope in:
- Move the `ctx.driver.stage(stem=ticket.stem, attempt=run.attempt, surface="check")` context, and its `event.end(result.outcome)`, from `run_stages` into `stages.check`. Every return path of `check` ends the stage with the returned result's outcome. `run_stages` keeps calling `check` exactly as it does today, with no `with` for check.
- New unit test `tests/unit/test_check_stage_events.py`: a fake driver whose `stage` records events shows that `stages.check` returns through an early return path (for example `check_candidates` refusing) with exactly one `stage_start` and one `stage_end`, and that the end's outcome equals the returned result's outcome.
- New integration test `tests/integration/test_check_meta_fill_stage.py`: build the `ctx` the way `tests/integration/test_host_mechanical.py` does (reuse its imports from `tests/integration/test_mergequeue.py` without editing that file). Set `ctx.config.meta.paths` to one test root. Commit on the ticket branch an edited file under that root whose `clutch:meta` hash no longer matches. Script `FakeLLM` with one valid `MetaReply` for that path, and run `stages.check`. Check completes without raising and the file's header purpose equals the scripted purpose.
- `docs/how-clutch-works.md`: fix the two sentences claiming that only resolve and review nest (the step list in section 7, "Resolve and its review may nest inside the merge stage on the same driver; other stages do not nest.", and the `engine.log` row in the state-files table). They now also name `review_visual` and the `meta` fill nesting inside Check.

Scope out: the `Driver.stage` allowlist itself (owned by `check-meta-fill-nested-stage`), how serve handles a worker exception, and `metafill.py`.

## Scope fence
- clutch/stages.py
- tests/unit/test_check_stage_events.py
- tests/integration/test_check_meta_fill_stage.py
- docs/how-clutch-works.md

## Acceptance criteria
1. `stages.check` returning through an early refusal emits exactly one `check` `stage_start` and one `stage_end` whose outcome equals the returned outcome, not zero events and not an end without a start; checked by `./dev.py test tests/unit/test_check_stage_events.py`.
2. With `meta.paths` configured and a drifted header in the diff, `stages.check` on a real `Driver` completes without raising `stage already open`, and the header purpose equals the `FakeLLM` scripted purpose; checked by `./dev.py test tests/integration/test_check_meta_fill_stage.py`.
3. `run_stages` contains no `driver.stage(` call with surface `check`; checked by `./dev.py test tests/unit/test_check_stage_events.py` asserting the engine-log sequence for one pipeline-style call has a single `check` start/end pair.
4. Existing Check and visual-review tests still pass under the moved stage; checked by `./dev.py test tests/integration/test_host_mechanical.py tests/integration/test_visual_review_spec.py tests/integration/test_image_candidates_select.py tests/unit/test_check_meta_fill.py tests/unit/test_driver_check_nesting.py`.

## Verification
```
./dev.py test tests/unit/test_check_stage_events.py tests/integration/test_check_meta_fill_stage.py tests/integration/test_host_mechanical.py tests/integration/test_visual_review_spec.py tests/integration/test_image_candidates_select.py tests/unit/test_check_meta_fill.py tests/unit/test_driver_check_nesting.py
```

## Definition of rejected
- A second `check` stage pair is emitted per Check in a pipeline run.
- The integration test stubs the `Driver` or `metafill.make_ask`.
- Edits outside the fence, including to `tests/integration/test_mergequeue.py` or `tests/integration/test_stages.py`.

## Time budget
- expected: 20m
- stuck: 40m
