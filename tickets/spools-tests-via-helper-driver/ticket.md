---
state: draft
source: human
priority: P3
kind: chore
---

## Depends on
- spools-test-helper
- spools-tests-via-helper

## Context
- docs/roadmap.md#6. Owner decisions (decided 2026-11-13)
- tests/spool_captures.py
- tickets/spools-tests-via-helper/ticket.md
- tickets/spools-test-helper/ticket.md
- clutch/evidence/store.py::capture_key
- clutch/driver.py::Spool
- tests/integration/test_driver.py

## Goal / Why
Roadmap row 194, the driver family of row 63's integration test split (the merge family was `spools-tests-via-helper`; the two fake-filesystem tests are the roadmap row `spools-tests-via-helper-fake-fs`). Row 63 (`spools-onto-evidence-store-r2`) makes `Spool` write through `put_capture` and stop writing `<state_dir>/spools/`; the helper body in `tests/spool_captures.py` flips there. Every test that builds a `spools/` path by hand breaks at the flip, so first these tests reach spool files through `read_capture`, `write_capture` and `list_captures`. No production file changes; the helper body still reads `spools/` exactly as `Spool.write` writes it, so there is one writer and no dual path.

Re-derived by grep over `tests/integration`, `tests/harness` and `tests/*.py` for `spools`, `Spool(`, `.spool` and `spool.root`, minus the files routed by `spools-tests-via-helper` and `spools-test-helper`, minus the two fake-filesystem files, about 30 sites in 11 files. The helper signatures are `read_capture(state_dir, spool_stem, attempt, name) -> bytes` (raises `CaptureNotFound` when absent, `CaptureUnreadable` on another OS error, `ValueError` on an invalid slot), `write_capture(state_dir, spool_stem, attempt, name, data: bytes)` and `list_captures(state_dir, spool_stem, attempt=None) -> sorted [(attempt, name)]`; the names are the names the caller passed to `Spool.write`, never `run-` prefixed. The stem and attempt of each site, read from `clutch/driver.py` (`spool_stem = f"{stem}/{run_seq}" if run_seq is not None else stem`, written at `Spool.write(spool_stem, attempt, f"{name}/prompt.md" ...)`, where `name` is `f"{stage.surface}{segment}/call-NN"`): a run with a ticket, or a ticketless run without `run_seq`, spools under the plain stem and the `attempt` argument; a ticketless run with `run_seq=n` spools under `<stem>/<n>` and its `attempt`. The path `spools/t-echo/1/implement/call-01/prompt.md` is stem `t-echo`, attempt `1`, name `implement/call-01/prompt.md`. Sites, each routed with its fact kept:

- `tests/integration/test_driver.py`: the module helper `spool(state_dir, stem="t-echo", attempt=1)` (line 118) builds the path and is called by 12 assertions. Delete it. Reads become `read_capture(state, "t-echo", 1, "implement/call-01/prompt.md").decode()` (same for `output.txt`, `error.txt`, `call-03`, the `review/call-01` pair, the two `[REDACTED:CLUTCH_TEST_KEY]` reads at `implement/call-01/prompt.md` and `implement/call-02/error.txt`). The `exists()` at line 183 and line 332 become a `read_capture` call (raises `CaptureNotFound` when absent). Line 332 is a ticketless run without `run_seq`: stem `triage`, attempt `1`, name `triage/call-01/prompt.md`. The negative at line 294 (`implement/call-05` absent) becomes: no name in `list_captures(state, "t-echo", 1)` starts with `implement/call-05/`, with a positive control in the same test that `implement/call-04/prompt.md` is listed (four calls were made, `len(llm.requests) == 1 + 3`).
- `tests/integration/test_kill_executor_abort.py` imports `spool` from `test_driver`. It is not in the family list but its import breaks when `spool` is deleted, so it is fenced: line 93 only passes `driver.spool.root.parent` as a workspace (no spool path asserted, left alone). Line 135 (`implement/call-01/output.txt` absent) and line 239 (`implement/call-02` absent) become listings filtered by that exact name or prefix and asserted empty, each with a positive control that `implement/call-01/prompt.md` is listed (the prompt is spooled at `clutch/driver.py` before the model call and the output after it, so a killed call has the first and not the second); the import drops `spool`.
- `tests/integration/test_echo_stage.py` line 110: stem `t-echo`, attempt 1, names `echo/call-01/prompt.md` and `echo/call-01/output.txt`; the `call` path variable goes away.
- `tests/integration/test_kill_worker_stop.py` line 129 and `tests/integration/test_kill_failure_suppression.py` line 97: `not (state / "spools/t-echo/1/implement/call-01/output.txt").exists()`, stem `t-echo`, attempt 1. Each becomes a listing filtered to that exact name asserted empty, with the positive control that `implement/call-01/prompt.md` is listed, verified by running the test before the control is kept; where the stage was killed before the prompt spool, the control names the one capture that test proves exists, and if none exists the test says so in `run.md` and keeps the filtered-empty assertion with the reason.
- `tests/integration/test_harvest_orphans.py` lines 49-51 write the fixture a harvest later reads: `write_capture(repo / ".clutch" / "state", STEM, attempt, "implement/error.txt", b"provider died with useful detail")`, replacing the `mkdir` and `write_text`.
- `tests/integration/test_rework.py` line 509: stem `original`, attempt 7, name `rework/call-01/prompt.md`; `read_capture(...).decode() == prompt`. The only site in the file.
- `tests/integration/test_triage.py` line 175: ticketless run with `run_seq=m.seq`, so stem `f"triage/{m.seq}"`, attempt 0, names `triage/call-01/prompt.md` and `triage/call-01/output.txt`, each read with `read_capture` (a missing one raises `CaptureNotFound`, which fails the test as the `exists()` did). Merged `index-box-neighbors-prompts` edited the version pins of this file only; the spool lines were not changed (read at HEAD).
- `tests/integration/test_eval_harness.py` line 329: stem `fixture-logic-pagination`, attempt 1, names `author/call-01/output.txt` (compared to `json.dumps(authored)`) and `author/call-01/prompt.md` (contains `fixture`), both with `read_capture(cfg.state_dir, ...).decode()`.
- `tests/integration/test_retro.py` lines 108 and 114: `not list(driver.spool.root.rglob("window.jsonl"))` for a ticketless run with `run_seq=window.sequence` (1) and `attempt=1`: stem `retro/1`, attempt 1. Each becomes: no name in `list_captures(c.config.state_dir, "retro/1", 1)` ends with `window.jsonl`, with the positive control that `retro/call-01/prompt.md` is listed (the retro prompt is spooled in both parametrized branches, so the listing is not empty). Lines 93-99 wrap `driver.spool._fs.write` to record write paths; they assert no spool path (`path in writes` is about the scratch file) and stay.
- `tests/integration/test_image_candidates_select.py` lines 96 and 180: `not (ctx.driver.spool.root / STEM / "0/render").exists()`: stem `STEM`, attempt 0. Each becomes: no name in `list_captures(ctx.config.state_dir, STEM, 0)` starts with `render/`, with a positive control that `review_visual/call-01/prompt.md` is listed at line 96 (`test_check_selects_or_parks` scripts two replies, so the model is called). Line 180 is `test_missing_visual_baseline_parks`, whose script is empty and which parks with `visual_undecided` before any model call, so it spools nothing under `review_visual`: the implementer lists `STEM` attempt 0 when running it, uses any capture that test really writes as the control, and if none exists keeps the filtered-empty `render/` assertion, records the reason in `run.md`, and the site is exempt from criterion 4 by name.

Left alone, with the reason: `tests/integration/test_watchdog.py` line 82 asserts `list((cfg.state_dir / "spools").rglob("events.jsonl")) == []` after a bare provider-client call; that call has no stem and attempt (no `Driver`, no `Spool`), the helper reads one stem and attempt and cannot enumerate every stem, and adding a list-all function changes the helper, which row 63 and the fake-filesystem ticket own. The assertion stays true after the flip (nothing writes `spools/`) and is named here so the owner knows it pins nothing then. `tests/integration/test_evidence_envelope.py` greps `clutch/` source and a docs table row for the text `spools/`, not a spool file. `tests/unit/` files that construct `Spool(` (`test_key_scope`, `test_review_panel_use`, `test_route_kinds_filter`, `test_driver_panel_fanout`, `test_projection_leftovers`) set a root and assert no path, or were routed by `spools-test-helper`. `test_daemon_composition.py:998` compares `ctx.driver.spool._fs is ctx.fs`, an identity, not a path.

## Boundary contract
### Routed driver-family spool assertions
- disposition: extend
- owner: the eleven test files in Scope fence
- consumers: the integration suite and, at the flip, `spools-onto-evidence-store-r2`
- observable change: each assertion or fixture reaches spool files through `read_capture`, `write_capture` or `list_captures` instead of a hand-built `spools/` path; the facts asserted (which file exists, its text) are unchanged and no assertion weakens
- compatibility: preserves the asserted facts; `tests/spool_captures.py`, its signatures and every production file are unchanged
- acceptance: criteria 1 to 4
- tests: the eleven files in Scope fence
- post-merge source of truth: tests/spool_captures.py for the `spools/` layout; the eleven files for the routed facts

## Scope in / Scope out
Scope in:
- Route the sites named in Goal through `tests/spool_captures.py`, plus the import each file needs. Nothing else in those files changes, except deleting `spool` from `test_driver.py` and from the import in `test_kill_executor_abort.py`.
- A positive existence or text assertion becomes a `read_capture` call. A negative assertion becomes a listing filtered by the same exact name or prefix and asserted empty, with a positive control in the same test that the listing is not vacuous; a control is verified by running the test, never assumed.
- No new test file and no new helper: the helper has its own test, `tests/unit/test_spool_captures.py`, this ticket adds no behavior, and the routed assertions are the tests. No test is added to a hot file. No `tests/unit/` test is touched, so none reads a repo file.

Scope out:
- All production code, every document, prompt specs, `tests/spool_captures.py` and `tests/unit/test_spool_captures.py`.
- The two fake-filesystem tests (`spools-tests-via-helper-fake-fs`), `test_watchdog.py` and the other files named as left alone.
- Merge order: confirmed or running tickets that fence these files edit meta headers or other lines (`meta-annotate-tests-integration-a`, `meta-annotate-tests-integration-b`, `cli-group-engine-run`, `move-serve-rig`, `tests-shared-fakes-a`, `stage-event-owner-stem`, `projection-leftovers`, `review-panel-r2`, `reply-parse-prose-before-json`, `checkout-carries-journal`, `harvest-usd-source-flags`, `redaction-harvest-seam`, `conflict-rerun-swap`, `rework-review-sees-siblings`, `review-panel-stage-use` and others); none is known to edit the `spools/` lines routed here, so either order leaves both applicable and a conflict at an import line is resolved by keeping both imports. `review-panel-stage-use-requisition` does not fence `test_rework.py`; `review-panel-stage-use` only runs it. `review-panel-stage-use-majority` (row 192) may fence `tests/integration/test_triage.py`; this ticket changes only its line 175 block, so either order applies. `spools-onto-evidence-store-r2` is a draft that fences `test_driver.py` and must list this ticket in `## Depends on` before it runs.

## Scope fence
- tests/integration/test_driver.py
- tests/integration/test_echo_stage.py
- tests/integration/test_kill_worker_stop.py
- tests/integration/test_kill_failure_suppression.py
- tests/integration/test_kill_executor_abort.py
- tests/integration/test_harvest_orphans.py
- tests/integration/test_rework.py
- tests/integration/test_triage.py
- tests/integration/test_eval_harness.py
- tests/integration/test_retro.py
- tests/integration/test_image_candidates_select.py

## Acceptance criteria
1. Single call site: `grep -n -E '"spools|spool\(|spool\.root' tests/integration/test_driver.py tests/integration/test_echo_stage.py tests/integration/test_kill_worker_stop.py tests/integration/test_kill_failure_suppression.py tests/integration/test_kill_executor_abort.py tests/integration/test_harvest_orphans.py tests/integration/test_rework.py tests/integration/test_triage.py tests/integration/test_eval_harness.py tests/integration/test_retro.py tests/integration/test_image_candidates_select.py` prints only the line 93 `driver.spool.root.parent` workspace argument in `test_kill_executor_abort.py`; no `"spools` literal and no call of the deleted `spool(` helper remains.
2. `./dev.py test tests/integration/test_driver.py tests/integration/test_echo_stage.py tests/integration/test_kill_worker_stop.py tests/integration/test_kill_failure_suppression.py tests/integration/test_kill_executor_abort.py tests/integration/test_harvest_orphans.py` passes, with the harvest reason still containing `provider died with useful detail`, and each kill-family negative still asserting that `implement/call-01/output.txt` (or `implement/call-02/`) is not listed, not that the listing is empty.
3. `./dev.py test tests/integration/test_rework.py tests/integration/test_triage.py tests/integration/test_eval_harness.py tests/integration/test_retro.py tests/integration/test_image_candidates_select.py` passes, with the rework spool still equal to the rendered prompt, the triage test still requiring both `prompt.md` and `output.txt` for every message, and the fixture capture still equal to `json.dumps(authored)`.
4. Every routed negative assertion (`test_driver.py` call-05, the two kill tests, `test_kill_executor_abort.py`, `test_retro.py`, `test_image_candidates_select.py` line 96; line 180 as named in Goal) pairs with a positive control that names a capture the same test shows exists, checked by `./dev.py test` on the files of criteria 2 and 3; and `git diff --stat` shows no file outside the fence, no file under `clutch/` and not `tests/spool_captures.py` changed, checked once in review.

## Verification
```
./dev.py test tests/integration/test_driver.py tests/integration/test_echo_stage.py tests/integration/test_kill_worker_stop.py tests/integration/test_kill_failure_suppression.py tests/integration/test_kill_executor_abort.py tests/integration/test_harvest_orphans.py tests/integration/test_rework.py tests/integration/test_triage.py tests/integration/test_eval_harness.py tests/integration/test_retro.py tests/integration/test_image_candidates_select.py
uv run ruff format --check .
```

## Definition of rejected
A production file, `tests/spool_captures.py`, a doc, or a file outside the fence changes; a routed assertion is weakened, deleted, or loosened (a negative with no positive control, or a listing asserted empty for the whole attempt); a test builds a `spools/` path or a second helper reads the layout; the helper gains a parameter or a second read path; a new test file or a new fixture is added to a hot file; or a SQLite file is opened.

## Time budget
- expected: 30m
- stuck: 60m
- reason: About 30 mechanical sites in 11 files with no new behavior; `./dev.py test` on 11 integration files is the slow part, and the helper and fake-filesystem work are separate tickets, so it is not split further.
