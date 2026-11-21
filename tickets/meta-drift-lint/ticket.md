---
state: draft
source: human
priority: P3
kind: feature
---

## Depends on
- meta-schema-and-refresh-r2

## Context
- clutch/meta.py
- clutch/gates.py
- clutch/stages.py::check_autofix
- clutch/stages.py::check_severity
- clutch/stages.py::Evidence
- clutch/stages.py::DiffBudgetGate
- tests/unit/test_images_gate.py
- tests/integration/test_gates.py::test_default_severity_is_all_hard_over_engine_codes
- tests/integration/test_closed_sets.py::test_gates_closed_sets_and_constants
- docs/annotations-index-plan.md#4. Drift

## On-demand
- docs/how-clutch-works.md

## Goal / Why
Roadmap row 71, ticket 3 of `docs/annotations-index-plan.md`. After this ticket Check keeps the metadata blocks of a ticket's changed files current and reports the ones a person or model still has to finish. Today a ticket that edits an annotated file leaves its `hash` stale until someone runs `clutch meta refresh` by hand, so `clutch meta check` on main lists drift that no ticket owned.

Check gains a step that runs after the autofix step and before evidence is gathered. It takes the files the branch changed (outside `tickets/`, still present in the worktree), runs `meta.check` on them, runs `meta.refresh` on them, and commits what refresh rewrote as `clutch(<stem>): meta` on the ticket branch. It then reports every changed file under `meta.paths` that still needs a person, through a new engine gate `meta_drift` that is soft by default. A host with `meta.paths: []` sees no step, no commit and no finding.

Each changed file under `meta.paths` gets at most one finding, with exactly one reason by this fixed mapping, first match wins:
- `malformed`: `meta.refresh` listed the file as malformed (the block does not follow the closed schema); refresh did not touch it.
- `empty_purpose`: after refresh the block's `purpose` is empty. This covers a file that had no block (refresh inserts one with an empty `purpose`) and a block whose `purpose` was already empty.
- `purpose_unverified`: before refresh `meta.check` reported the file `drifted` (its body moved since the block was stamped), and its `purpose` is nonempty. Refresh restamped the hash, but a drifted `purpose` cannot be detected mechanically, so the gate says the text was not re-read.
- No finding otherwise, including a file whose block is current.

Every changed file under `meta.paths` goes through this mapping; the gate does not look only at the reasons named here. `meta_drift` is soft: a failing gate is recorded in `checks.json` and Review sees the `meta` commit in the diff; it never changes the Check outcome by itself.

## Boundary contract
### Engine gate vocabulary
- disposition: extend
- owner: clutch/gates.py (`ENGINE_GATE_CODES`, `DEFAULT_GATE_SEVERITY`)
- consumers: `merge_severity`, `run_gates`, ticket `gate_bypass` validation in `clutch/tickets.py`, the scorecard's engine-code filter, `review.gate_severity` overrides
- observable change: `meta_drift` joins `ENGINE_GATE_CODES`, and `DEFAULT_GATE_SEVERITY["meta_drift"]` is `soft` while every other code stays `hard`; `review.gate_severity: {meta_drift: hard}` makes it hard and a ticket `gate_bypass` entry for it is accepted
- compatibility: the eleven existing codes and their `hard` severity are unchanged; a host config loads unchanged; `meta_drift` is not in `CHECK_GATES`, so the merge-time gate runs in `clutch/mergequeue.py` do not run it
- acceptance: the severity default and the closed vocabulary are pinned by the two existing tests this ticket updates
- tests: `tests/integration/test_gates.py` and `tests/integration/test_closed_sets.py` updated; new unit test for the gate
- post-merge source of truth: clutch/gates.py

### Check meta step and gate
- disposition: extend
- owner: clutch/stages.py (`check`, beside `check_autofix`; `Evidence`; the gate classes beside `DiffBudgetGate`)
- consumers: every Check run; `checks.json` readers (Review, retro, scorecard); `clutch/meta.py` is reused unchanged through `meta.check` and `meta.refresh`
- observable change: Check commits `clutch(<stem>): meta` on the ticket branch when refresh rewrote a file; `Evidence` gains `meta_findings: list[Finding] = []`; a new `MetaDriftGate` with code `meta_drift` reports them and runs in Check only, after the existing gates; the Check outcome mapping is: only `meta_drift` findings (soft) leave the outcome `ok`; with `meta_drift` hard by override or any other hard failure the outcome is `gate_failed`
- compatibility: Check for a host with empty `meta.paths`, or a branch that changes no file under it, runs no meta step and writes no commit; `CHECK_GATES`, the merge-time gate sequence and every existing gate's report are unchanged; refresh and check behavior in `clutch/meta.py` is unchanged
- acceptance: the unit tests named in the criteria below
- tests: new unit tests with fakes for git and the in-memory/tmp filesystem
- post-merge source of truth: clutch/stages.py

## Scope in / Scope out
Scope in:
- `clutch/gates.py`: add `meta_drift` to `ENGINE_GATE_CODES`; make `DEFAULT_GATE_SEVERITY` `soft` for `meta_drift` and `hard` for every other code (a one-line set of soft defaults beside the map, not a second map).
- `clutch/stages.py`: add `meta_findings: list[Finding] = []` to `Evidence`; add `MetaDriftGate` (code `meta_drift`, reports `artifact.meta_findings`, a failing report when any exist) beside `DiffBudgetGate`; add `async def check_meta(ctx, ticket) -> list[Finding]`, which does the step described in Goal / Why using `ctx.git.diff_names`, `ctx.git.ls_files`, `ctx.git.rev_parse` and `ctx.git.commit(..., only=changed)` and `clutch/meta.py`'s `check` and `refresh` with the worktree as root and `ctx.fs`; when the filtered changed-file list (outside `tickets/`, present in the worktree) is empty it returns `[]` without calling `meta.check` or `meta.refresh`, because both treat an empty `paths` as every file under `meta.paths` and would rewrite the whole annotated tree; each finding has code `meta_drift`, the path, message `<path>: <reason>` and a paved road per reason (`malformed`: fix or remove the block so it has the schema plus the six keys with a valid kind; `empty_purpose`: run `clutch meta fill <path>` or write the one-line purpose; `purpose_unverified`: reread the purpose against the new content and rerun `clutch meta fill <path>` if it is stale). In `check`, call it right after the autofix step when `ctx.config.meta.paths` is nonempty, put its result in `Evidence` with `model_copy(update={"meta_findings": ...})` beside `render_failed`, and run the gates as `run_gates((*CHECK_GATES, *CHECK_ONLY_GATES), ...)` where `CHECK_ONLY_GATES = (MetaDriftGate(),)` is a new tuple beside `CHECK_GATES`, which stays unchanged.
- `docs/how-clutch-works.md`: add the meta step to the Check list in section 4.3 as a new item after the autofix item; add `clutch(<stem>): meta` beside `autofix` in the sentence that lists Check's branch commits (section 4, the line ending "not on `main`"); add a `meta_drift` row to the Check gates table in 5.1; change "Every engine gate is hard by default." to say `meta_drift` is soft by default and every other engine gate is hard. Nothing else in that document changes.
- The two existing pins the changes flip: `tests/integration/test_gates.py::test_default_severity_is_all_hard_over_engine_codes` (all hard except `meta_drift`) and `tests/integration/test_closed_sets.py::test_gates_closed_sets_and_constants` (the severity dict and the code set gain `meta_drift`). `tests/unit/test_stages_render_check.py` and `tests/unit/test_images_gate.py` build a fake `ctx.config` that has only `review`; each gains `meta=SimpleNamespace(paths=[])` on that config, the one edit the new `ctx.config.meta.paths` read forces there.
- New tests: `tests/unit/test_meta_drift_gate.py` and `tests/unit/test_meta_drift_check.py`.

Scope out: `clutch/meta.py` and `clutch/metafill.py` (reused, not changed); running the step at merge or adding `meta_drift` to `CHECK_GATES`; making the gate hard; comparing against the base branch's block; the host contract guide (its "engine defaults are all hard" wording is corrected by a later ticket once `index-config-touches`, which fences that file, has merged); `clutch/help.py`, the VS Code extension and any command (no verb is added or changed); the index tickets `index-build-r2` and `context-suggest`.

Merge order: `index-config-touches` and `spools-scratch-dir` are confirmed and unmerged. `index-config-touches` fences none of this ticket's files. `spools-scratch-dir` fences `docs/how-clutch-works.md` (a scheduler shared path), `clutch/stages.py`, `tests/unit/test_stages_render_check.py` and `tests/unit/test_images_gate.py`; it edits spool paths and I edit a different line of each (the `Evidence` class, `check`, the gate classes, the section 4.3 and 5.1 text, and the fake `config=` lines), so either order merges cleanly, and neither ticket's criteria depend on the other's.

## Scope fence
- clutch/gates.py
- clutch/stages.py
- docs/how-clutch-works.md
- tests/integration/test_gates.py
- tests/integration/test_closed_sets.py
- tests/unit/test_stages_render_check.py
- tests/unit/test_images_gate.py
- tests/unit/test_meta_drift_gate.py
- tests/unit/test_meta_drift_check.py

## Acceptance criteria
1. `tests/unit/test_meta_drift_gate.py` asserts `DEFAULT_GATE_SEVERITY["meta_drift"] == "soft"`, that the other eleven codes are `"hard"`, and that `merge_severity(None)["meta_drift"] == "soft"`; a gate default of `hard` for `meta_drift` fails it. Check: `./dev.py test tests/unit/test_meta_drift_gate.py`.
2. `tests/unit/test_meta_drift_gate.py` runs `run_gates` with `MetaDriftGate()` over an `Evidence` carrying one `meta_findings` entry and asserts the result `passed` is `True` and `soft_failures` has one `meta_drift` report; with severity `{"meta_drift": "hard"}` it asserts `passed` is `False` and `hard_failures` has the report; with `meta_findings=[]` it asserts a `pass` verdict. A gate that fails hard by default, or a pass with findings, fails it. Check: `./dev.py test tests/unit/test_meta_drift_gate.py`.
3. `tests/integration/test_gates.py::test_default_severity_is_all_hard_over_engine_codes` and `tests/integration/test_closed_sets.py::test_gates_closed_sets_and_constants` pass with `meta_drift` in the code set and `soft` as its only soft default. Check: `./dev.py test tests/integration/test_gates.py tests/integration/test_closed_sets.py`.
4. `tests/unit/test_meta_drift_check.py` builds a `tmp_path` worktree with `meta.paths: [{root: docs/, kind: plan}]`, a fake `git` returning changed files and `ls_files`, and calls `check_meta`. It asserts one finding per path with exactly these reasons: a changed `docs/new.md` with no block gives `docs/new.md: empty_purpose`; a changed `docs/old.md` whose block has a nonempty `purpose` and a stale `hash` gives `docs/old.md: purpose_unverified`; a changed `docs/bad.md` with a broken block gives `docs/bad.md: malformed` and its bytes are unchanged; a changed `docs/ok.md` whose block is current with a nonempty `purpose` gives no finding. A changed `docs/old.md` with a stale `hash` and an empty `purpose` gives `empty_purpose`, not `purpose_unverified`. Reporting `drifted`, `missing` or two findings for one path fails it. Check: `./dev.py test tests/unit/test_meta_drift_check.py`.
5. `tests/unit/test_meta_drift_check.py` asserts that after criterion 4's run the files refresh rewrote (`docs/new.md`, `docs/old.md`) now hold a current `hash`, that the fake `git.commit` was called once with message `clutch(work): meta` and `only` equal to exactly the refreshed paths, and that on a second `check_meta` call over the same tree no commit is made and `docs/old.md` yields no finding. A commit that includes `docs/bad.md` or `docs/ok.md`, or one commit per file, fails it. Check: `./dev.py test tests/unit/test_meta_drift_check.py`.
6. `tests/unit/test_meta_drift_check.py` builds `meta.paths: [{root: docs/, kind: plan}]` with a tracked `docs/untouched.md` that has no block, and `docs/stale.md` with a stale `hash`, neither changed on the branch, and the only changed files `src/a.py`, a file under `tickets/work/` and a path deleted in the worktree; it asserts `check_meta` returns `[]`, `git.commit` is not called and the bytes of `docs/untouched.md` and `docs/stale.md` are unchanged; an implementation that calls `meta.refresh` with an empty `paths` fails it. The same file asserts that a changed file outside `meta.paths` (`src/a.py`), a changed file under `tickets/work/`, and a changed path deleted in the worktree are never read or rewritten and yield no finding, and that with `meta.paths` empty `check` makes no `git.commit` call and no `meta_drift` report. Check: `./dev.py test tests/unit/test_meta_drift_check.py`.
7. `tests/unit/test_meta_drift_check.py` drives `stages.check` with `gather_evidence`, `check_hosts` and `lift_outbox` patched (the pattern of `tests/unit/test_images_gate.py`), a changed `docs/new.md` with no block, and default severity; it asserts `result.outcome == "ok"`, a report with code `meta_drift` and verdict `fail` in `result.artifact.reports`, and `result.artifact.passed` is `True`. With severity `meta_drift: hard` the same run asserts `result.outcome == "gate_failed"`. A soft failure that ends the attempt, or a missing report, fails it. Check: `./dev.py test tests/unit/test_meta_drift_check.py`.
8. `tests/unit/test_stages_render_check.py tests/unit/test_images_gate.py` pass with the fake config carrying `meta=SimpleNamespace(paths=[])`. Check: `./dev.py test tests/unit/test_stages_render_check.py tests/unit/test_images_gate.py`.
9. `docs/how-clutch-works.md` section 5.1 has a `meta_drift` row, says `meta_drift` is soft by default, and section 4.3 lists the meta step, read by eye in review.

## Verification
```
./dev.py test tests/unit/test_meta_drift_gate.py tests/unit/test_meta_drift_check.py tests/unit/test_stages_render_check.py tests/unit/test_images_gate.py tests/unit/test_meta_refresh.py tests/unit/test_meta_cli.py
./dev.py test tests/integration/test_gates.py tests/integration/test_closed_sets.py tests/integration/test_bug_gate.py tests/integration/test_host_mechanical.py tests/integration/test_hostfiles.py tests/integration/test_scorecard.py
```

## Definition of rejected
`meta_drift` is hard by default, is added to `CHECK_GATES` or run at merge, or the step runs when `meta.paths` is empty. Check commits any file other than the ones `meta.refresh` rewrote, commits on `main`, or writes a block itself instead of calling `meta.refresh`. A changed file gets two findings or a reason outside `malformed`, `empty_purpose` and `purpose_unverified`. `clutch/meta.py`, `clutch/metafill.py`, the host contract guide or any command or help text changes. A new config knob or a second severity map is added.

## Time budget
- expected: 25m
- stuck: 50m
