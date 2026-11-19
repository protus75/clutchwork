---
state: confirmed
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- merge-admission-single-owner

## Context
- tickets/merge-model-resolve/evidence/merge-conflict-facts.md
- clutch/mergequeue.py::ConflictHandoff
- clutch/mergequeue.py::MergeQueue._facts
- clutch/mergequeue.py::MergeQueue._resolve
- clutch/mergequeue.py::MergeQueue._admit
- clutch/specs/__init__.py::ENGINE_LLM_SURFACES
- clutch/stages.py::review_stage
- clutch/runner.py::drive
- clutch/driver.py::Driver.stage
- tests/integration/test_daemon_composition.py::production_writer

## On-demand
- clutch/git.py
- docs/how-clutch-works.md

## Goal / Why
When the mechanical step (`merge.strategies`) cannot resolve a rebase conflict in the serve merge queue, a model now tries a bounded repair before the existing hand-off to Rework. This is step 2 of the three conflict steps in `docs/parallel-tickets-plan.md` section 5. It lands only step 2. The discard-and-rerun step and the removal of `ConflictHandoff` belong to `conflict-discard-rerun`, so every refusal in this ticket (ineligible conflict, `decline`, review `snag`, malformed reply) returns the existing `ConflictHandoff` unchanged.

What is true after the ticket:
- A new prompt spec `clutch/specs/resolve.md` (surface `resolve`) receives this ticket's Goal and Scope in, the Goal and Scope in of each ticket whose commit on main since the merge base touched a conflicted path, and the base, ours and theirs text of each conflicted file. It returns resolved file contents or `decline` with a reason.
- Engine-constant bounds gate the call: at most 3 conflicted files and 60 conflict-marker lines in total across the admission; text files only; no modify/delete or rename conflict; no conflicted path matching `engine_plane_safety_inventory`. A path in `scheduler.parallel.shared_paths` is exempt only from the safety-inventory test, never from the other bounds, and only when that config field exists on main (see Scope in).
- A model resolution is not a clean rebase, so the pinned approval does not carry over. One call of the existing `review` surface, through `stages.review_stage` with the resolution delta as its `diff` input, must approve before the candidate goes on to the safety and integration tiers. `snag` or any non-approve outcome hands off as above.
- `merge_conflict_facts` records `resolving_rung: model` when a model resolution was kept and the candidate continued.

Why it matters: parallel runs in `serve` will manufacture conflicts, and today every one of them becomes a full Rework of the ticket. The evidence file shows this repo has recorded zero conflicts of any kind in 566 merges, and the plan's "13 `merge_conflict_facts` events" are 13 `requisition_verdict` text matches. So the bounds are design choices with no empirical calibration. They are named constants that the first real `model` facts can retune.

## Boundary contract
### Merge queue conflict ladder
- disposition: extend
- owner: clutch/mergequeue.py
- consumers: serve admission through `MergeQueue._admit`, `daemon.consume_handoff`, `clutch/retro.py` reading `CONFLICT_FACTS`
- observable change: after a git conflict that `_resolve` cannot settle mechanically, `_admit` runs the model step when the bounds allow it. On success the rebase continues and the candidate takes the existing safety and integration tiers. On any refusal it aborts the rebase and returns `ConflictHandoff` exactly as today. `inline merge` (`conflict_ladder=False`) is unchanged and never calls the model.
- compatibility: `ConflictHandoff`, its fields and its consumers are unchanged. Existing `resolving_rung` values `none`, `mechanical` and `rework` keep their meaning. `model` is added. The journal fold still accepts all of them.
- acceptance: eligible conflict plus approved resolution continues to merge; each refusal path returns `ConflictHandoff` with the rebase aborted.
- tests: new `tests/unit/test_merge_resolve.py` (bounds, marker counting) and `tests/integration/test_merge_model_resolve.py` (admission paths with a fake LLM)
- post-merge source of truth: clutch/mergequeue.py

### Resolve prompt spec
- disposition: create
- owner: clutch/specs/resolve.md
- consumers: `MergeQueue._admit` model step only
- observable change: a new LLM surface `resolve` that returns resolved file contents or `decline`
- compatibility: no existing spec or surface changes. `clutch/specs/review.md` stays wired unchanged. `clutch/specs/rework.md` is untouched in this ticket, and its conflict-only-repair prohibition is removed by `conflict-discard-rerun`.
- acceptance: spec lint passes; the surface is in `ENGINE_LLM_SURFACES` and in every closed list that names the engine surfaces
- tests: `tests/unit/test_specs.py` pin and surface lists, `tests/unit/test_step_names_cover_surfaces.py`
- post-merge source of truth: clutch/specs/resolve.md
- closest existing: `clutch/specs/rework.md` (rewrites a ticket's work from findings) and `clutch/specs/review.md` (verdict on a diff)
- earning reason: neither takes conflict hunks as input or returns file contents; the rework spec forbids conflict-only repair; the review spec's input and output are pinned by the review baseline. The new spec is an independently versioned prompt contract with one production consumer and its own fake in tests.

### Surface and rung vocabularies
- disposition: extend
- owner: clutch/specs/__init__.py
- consumers: clutch/observe.py, clutch/stats.py, clutch/help.py, and tests that list the engine surfaces, vscode-clutchwork/extension.js (step icon table)
- observable change: `resolve` joins the engine LLM surfaces with a display label and help entry
- compatibility: existing surface names and labels are unchanged
- acceptance: every list that carries the engine surfaces carries `resolve`
- tests: the closed-set and step-name tests listed in the fence
- post-merge source of truth: clutch/specs/__init__.py

## Scope in / Scope out
Scope in:
- `clutch/specs/resolve.md`, version `1.0`, following the section layout of the existing review spec (read it from the worktree). Fence a pin for it in `tests/unit/test_specs.py`.
- Add `resolve` to `ENGINE_LLM_SURFACES` in `clutch/specs/__init__.py`. Then grep `clutch/` and `tests/` for `requisition_review` and for the collection names, and make the minimum edit in each fenced file whose list or label table must name `resolve`: `clutch/observe.py`, `clutch/stats.py`, `clutch/help.py`, `tests/unit/test_specs.py`, `tests/unit/test_step_names_cover_surfaces.py`, `tests/integration/test_closed_sets.py`, `tests/integration/test_watch_surface_tier.py`. A file that only mentions `requisition_review` and compares no surface list stays untouched.
- In `clutch/mergequeue.py`: named constants for the bounds (3 files, 60 marker lines), a pure eligibility function over the conflicted paths, their stage contents and the safety inventory, the model step inside the existing `GitError` branch of `_admit` after `_resolve` returns findings, the re-review through `stages.review_stage` without writing a review record or lifting an outbox, and the `model` value in `_facts`. A model call goes through `ctx.driver.run` with the spec's tier and effort.
- The input for other tickets' Goal and Scope in: `git log` of main from the merge base over the conflicted paths, subjects naming `clutch(<stem>)`, then read each stem's `tickets/<stem>/ticket.md` from main. A commit whose subject names no stem is omitted.
- `clutch/git.py`: only the wrapper methods the step needs (a path-limited log, the range-diff or path-limited diff for the delta). Reuse existing methods where they exist.
- `docs/how-clutch-works.md`: update only the 7.2.1 step 1 text that says anything else "hands the ticket to Rework", and add the model step and its re-review there.
- `shared_paths`: `scheduler.parallel.shared_paths` exists on main (`clutch/config.py`, merged by `parallel-config`); read it from config. Do not change the config model.
- `vscode-clutchwork/extension.js`: add `resolve_start`, `resolve_ok` and `resolve_failed` to the Recent Steps icon lookup table with one codicon no other step uses, and the same passed/failed colors as the other steps; `tests/integration/test_step_icons.py` requires an icon for every `STEP_KINDS` key.
- Serve runs admission inside the driver's open `merge` stage (`clutch/runner.py::drive`), and `Driver.stage` refuses nesting (`docs/how-clutch-works.md`: stages do not nest on one driver). Implement chooses one and names it in the run record: (a) end the merge stage before the resolve and review calls and reopen it after, keeping stages non-nesting (preferred); or (b) let `Driver.stage` allow these two surfaces nested and update that docs line. Edit `runner.py`/`driver.py` only as far as the chosen option needs.
- Minimal assertion edits forced by the new step: `tests/integration/test_daemon_composition.py` (the `not ctx.driver.llm.requests` check in `test_production_consumes_conflict_handoff_after_unwind`) and `tests/integration/test_rework.py::test_admission_never_invokes_rework_inline`. Each may allow one scripted `resolve` decline before the `ConflictHandoff`, and must keep its no-inline-Rework and no-approval-reuse checks.

Scope out:
- Discard-and-rerun, `ConflictHandoff` removal, `consume_handoff`, the `rework()` handoff parameter, the rework spec, the implement spec, the `prior-diff` lift.
- The review spec (wired unchanged).
- The stages module (`review_stage` is called as is).
- Inline merge (`drain`, `run`) conflict handling and its missing conflict paths in the facts, which the evidence file flags as a measurement gap. File it as a Suggestion Box item, not here.
- Correcting the false "13 events" claim in the roadmap and the parallel plan document; the evidence file lists the sites.
- New tests in existing hot test files (`tests/integration/test_mergequeue.py`, `test_stages.py`, `test_drain.py`, `test_daemon_composition.py`). New tests go in the two new files; a fake LLM and git rig for them live in those new files. The two assertion edits in Scope in are the only allowed edits there.

## Scope fence
- clutch/specs/resolve.md
- clutch/specs/__init__.py
- clutch/mergequeue.py
- clutch/git.py
- clutch/observe.py
- clutch/stats.py
- clutch/help.py
- vscode-clutchwork/extension.js
- docs/how-clutch-works.md
- tests/unit/test_merge_resolve.py
- tests/integration/test_merge_model_resolve.py
- tests/unit/test_specs.py
- tests/unit/test_step_names_cover_surfaces.py
- tests/integration/test_closed_sets.py
- tests/integration/test_watch_surface_tier.py
- tests/unit/test_help.py
- clutch/runner.py
- clutch/driver.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_rework.py
- tickets/merge-model-resolve

## Acceptance criteria
1. A pure bounds function rejects a conflict set with 4 files, and accepts one with 3 files; a unit test in `tests/unit/test_merge_resolve.py` checks both and fails if the limit is 4 or unlimited, run by `./dev.py test tests/unit/test_merge_resolve.py`.
2. The same function rejects 61 conflict-marker lines in total and accepts 60, rejects a binary file (NUL byte), a modify/delete conflict and a rename conflict, and rejects a path under `engine_plane_safety_inventory`; each case is its own assertion in `tests/unit/test_merge_resolve.py`, so a pass on the wrong bound fails.
3. With a fake LLM returning resolved contents and a fake review returning `approve`, `MergeQueue._admit` finishes with an ok `StageResult`, not a `ConflictHandoff`, and the journal holds a `merge_conflict_facts` signal with `resolving_rung` equal to `model`, not `rework`; checked by `./dev.py test tests/integration/test_merge_model_resolve.py`.
4. With the fake LLM replying `decline`, the result is a `ConflictHandoff` whose findings name the decline reason, the rebase is aborted (no `rebase-merge` directory in the worktree), and the signal carries `resolving_rung` equal to `rework`; checked in `tests/integration/test_merge_model_resolve.py`.
5. With resolved text that still contains a conflict marker, the result is a `ConflictHandoff` and the worktree's files are not staged; the test asserts `<<<<<<<` is not in any staged file, in `tests/integration/test_merge_model_resolve.py`.
6. With a fake review returning `snag`, the result is a `ConflictHandoff` and no `review.md` is written in the worktree or on main; checked in `tests/integration/test_merge_model_resolve.py`.
7. The model is not called when the bounds reject the conflict or when `conflict_ladder=False`; the fake LLM's call count is 0 in both cases, asserted in `tests/integration/test_merge_model_resolve.py`.
8. The `resolve` spec lints clean, has `llm_surface: resolve`, version `1.0`, at most 200 lines, and appears in `ENGINE_LLM_SURFACES`; `./dev.py test tests/unit/test_specs.py tests/unit/test_step_names_cover_surfaces.py tests/integration/test_closed_sets.py tests/unit/test_help.py` exits 0.
9. The 7.2.1 section of `docs/how-clutch-works.md` no longer says every non-mechanical conflict goes straight to Rework; reviewed once by reading the section. No test pins its text.
10. Existing queue behavior is preserved: `./dev.py test tests/integration/test_mergequeue.py tests/integration/test_merge_admission_owner.py` exits 0 with no edit to those files.
11. In `tests/unit/test_merge_resolve.py`, a path listed in `shared_paths` under the safety inventory is accepted by the bounds function, while the same path is still rejected at 4 files, at 61 marker lines, and when binary; run by `./dev.py test tests/unit/test_merge_resolve.py`.
12. In `tests/integration/test_merge_model_resolve.py`, a fake LLM reply that fails the resolve schema returns a `ConflictHandoff` with the rebase aborted and `resolving_rung` equal to `rework`, not an exception or an ok result.
13. `tests/unit/test_merge_resolve.py` runs the new `clutch/mergequeue.py` lines through fakes (a fake git, driver and ctx, injected so no real git process starts): the model step's decline, approve and malformed paths, and `_facts` returning `model`; any new `clutch/git.py` wrapper method gets a unit test with a fake runner, or the change reuses `_run` instead. `./dev.py test tests/unit/test_merge_resolve.py` passes and the `[coverage.files]` floors for both files hold in the unit gate.
14. In `tests/integration/test_merge_model_resolve.py`, an eligible conflict driven through the serve path (`runner.drive` with queue admission, reusing `production_writer` by import) runs the resolve and review calls without a "stage already open" error and merges with `resolving_rung` equal to `model`.

## Verification
```
./dev.py test tests/integration/test_daemon_composition.py tests/integration/test_rework.py tests/integration/test_step_icons.py tests/unit/test_merge_resolve.py tests/integration/test_merge_model_resolve.py tests/unit/test_specs.py tests/unit/test_step_names_cover_surfaces.py tests/integration/test_closed_sets.py tests/integration/test_watch_surface_tier.py tests/unit/test_help.py tests/integration/test_help.py tests/integration/test_mergequeue.py tests/integration/test_merge_admission_owner.py
```

## Definition of rejected
- A model resolution that continues to the safety tier without a review call approving the delta.
- Any change that removes or alters `ConflictHandoff`, `consume_handoff` or the Rework path, or that edits the review spec or the rework spec.
- Bounds read from config instead of engine constants, or a model call on the inline-merge path.
- New tests added to `tests/integration/test_mergequeue.py` or another hot test file.

## Time budget
- expected: 30m
- stuck: 60m
