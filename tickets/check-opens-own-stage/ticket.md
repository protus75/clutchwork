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
- clutch/driver.py::Spool
- clutch/metafill.py
- clutch/llm.py::FakeLLM
- clutch/seams.py::FileSystem
- clutch/ioguard.py
- tests/integration/conftest.py
- tests/fakes.py
- tests/git_fake.py
- tests/unit/test_driver_panel_fanout.py
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

### Check meta file reads
- disposition: reuse
- owner: clutch/seams.py
- consumers: clutch/stages.py::check_meta
- observable change: `check_meta` decides whether a changed path still exists through `ctx.fs` (the `FileSystem` seam that `meta.check`, `meta.refresh` and `metafill.fill` already read and write through) instead of a raw `Path.is_file()` call, so an in-memory `FileSystem` drives the whole meta branch
- compatibility: with `LocalFileSystem` the selected files are unchanged; deleted paths are still skipped
- acceptance: criterion 2
- tests: tests/integration/test_check_meta_fill_stage.py, tests/unit/test_check_meta_fill.py, tests/unit/test_meta_drift_check.py
- post-merge source of truth: clutch/seams.py

## Scope in / Scope out
Scope in:
- Move the `ctx.driver.stage(stem=ticket.stem, attempt=run.attempt, surface="check")` context, and its `event.end(result.outcome)`, from `run_stages` into `stages.check`. Every return path of `check` ends the stage with the returned result's outcome. `run_stages` keeps calling `check` exactly as it does today, with no `with` for check.
- In `check_meta`, replace the raw `(worktree / path).is_file()` filter with a check through `ctx.fs` (for example, the path's name is in `ctx.fs.entries((worktree / path).parent)`). The meta fill reads and writes file content only through `ctx.fs` (`meta.check`, `metafill.fill`, `meta.refresh`); this filter was the one raw disk read in that branch, and it made an in-memory filesystem skip every file.
- New unit test `tests/unit/test_check_stage_events.py`: a fake driver whose `stage` records events shows that `stages.check` returns through an early return path (for example `check_candidates` refusing) with exactly one `stage_start` and one `stage_end`, and that the end's outcome equals the returned result's outcome.
- New integration test `tests/integration/test_check_meta_fill_stage.py`. It runs under the integration I/O guard, so it is not added to `REAL_IO_TESTS` or `DISK_IO_SKIP` and uses no real git or disk writes. Build a real `Driver` the way `tests/unit/test_driver_panel_fanout.py` does: `FakeLLM`, `FakeJournal`, a `Spool` over `FakeFileSystem`, and a recording log. Use `GitFake` from `tests/git_fake.py` for `ctx.git`, with `diff_names` and `ls_files` returning the edited path. Set `ctx.fs` to a `FakeFileSystem` holding, under one `meta.paths` root in the worktree, an edited file whose `clutch:meta` hash no longer matches. Point `ctx.specs_dir` at the shipped `clutch/specs` directory through a `Path(__file__)` anchor (reads are allowed by the guard). Script `FakeLLM` with one valid `MetaReply` for that path, and run `stages.check` with an `ok` slip and empty `verification`. The test may replace `gather_evidence`, `check_hosts`, `lift_outbox` and `CHECK_GATES` the way `tests/unit/test_meta_drift_check.py::test_check_outcome` does, because they run after the meta fill. Check completes without raising, the file's header purpose read back from `ctx.fs` equals the scripted purpose, and `GitFake` records a `commit` with message `clutch(<stem>): meta`.
- Give the stub drivers in `tests/unit/test_meta_drift_check.py`, `tests/unit/test_images_gate.py` and `tests/unit/test_stages_render_check.py`, which call `stages.check` directly, a `stage` context manager whose yielded event has `end`. They now go through the moved stage.
- `docs/how-clutch-works.md`: fix the two sentences claiming that only resolve and review nest (the step list in section 7, "Resolve and its review may nest inside the merge stage on the same driver; other stages do not nest.", and the `engine.log` row in the state-files table). They now also name `review_visual` and the `meta` fill nesting inside Check.

Scope out: the `Driver.stage` allowlist itself (owned by `check-meta-fill-nested-stage`), how serve handles a worker exception, `metafill.py`, `tests/integration/conftest.py`, and the skipped `tests/integration/test_host_mechanical.py` and `tests/integration/test_image_candidates_select.py`.

## Scope fence
- clutch/stages.py
- tests/unit/test_check_stage_events.py
- tests/integration/test_check_meta_fill_stage.py
- tests/unit/test_meta_drift_check.py
- tests/unit/test_images_gate.py
- tests/unit/test_stages_render_check.py
- docs/how-clutch-works.md

## Acceptance criteria
1. `stages.check` returning through an early refusal emits exactly one `check` `stage_start` and one `stage_end` whose outcome equals the returned outcome, not zero events and not an end without a start; checked by `./dev.py test tests/unit/test_check_stage_events.py`.
2. With `meta.paths` configured and a drifted header in the diff, `stages.check` on a real `Driver` with `FakeLLM`, `GitFake` and `FakeFileSystem` completes under the integration I/O guard without raising `stage already open`, the header purpose read from `ctx.fs` equals the `FakeLLM` scripted purpose, and `GitFake` records the `meta` commit; checked by `./dev.py test tests/integration/test_check_meta_fill_stage.py`.
3. `run_stages` contains no `driver.stage(` call with surface `check`; checked by `./dev.py test tests/unit/test_check_stage_events.py` asserting the engine-log sequence for one pipeline-style call has a single `check` start/end pair.
4. Existing Check, meta-fill and visual-review tests that run (none in `DISK_IO_SKIP`) still pass under the moved stage; checked by `./dev.py test tests/unit/test_meta_drift_check.py tests/unit/test_images_gate.py tests/unit/test_stages_render_check.py tests/unit/test_check_meta_fill.py tests/unit/test_driver_check_nesting.py tests/integration/test_visual_review_spec.py`.

## Verification
```
./dev.py test tests/unit/test_check_stage_events.py tests/integration/test_check_meta_fill_stage.py tests/unit/test_meta_drift_check.py tests/unit/test_images_gate.py tests/unit/test_stages_render_check.py tests/unit/test_check_meta_fill.py tests/unit/test_driver_check_nesting.py tests/integration/test_visual_review_spec.py
```

## Definition of rejected
- A second `check` stage pair is emitted per Check in a pipeline run.
- The integration test stubs the `Driver` or `metafill.make_ask`, runs real git, or writes to disk.
- The integration test is added to `REAL_IO_TESTS` or `DISK_IO_SKIP`, or `tests/integration/conftest.py` is edited.
- Edits outside the fence, including to `tests/integration/test_mergequeue.py`, `tests/integration/test_stages.py` or `tests/integration/test_host_mechanical.py`.

## Time budget
- expected: 20m
- stuck: 40m