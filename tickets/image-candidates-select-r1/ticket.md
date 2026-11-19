---
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
source: box:roadmap_row
state: draft
---

## Depends on
- visual-review-surface
- image-quality-gate-wiring

## Context
- clutch/visual.py
- clutch/images.py
- clutch/runner.py::failure_terminal
- clutch/drain.py::reofferable
- docs/gemini-graphics-refactor-plan.md

## On-demand
- clutch/stages.py
- clutch/specs/implement.md
- docs/how-clutch-works.md

## Goal / Why
Roadmap row 54, Gemini plan B6 (Layer 3). `parse_render` accepts several `- artifact:` bullets, so a `kind: graphics` ticket in `mode: generate` can declare more than one deliverable. Today Implement writes the artifact paths directly, and nothing ranks candidates, selects one per artifact, or parks an undecidable result. This ticket handles every declared artifact on its own: each artifact gets its own candidate path, its own ranking and its own selection. After it:

(a) In `generate` mode Implement writes `candidates:` images (default 3) per declared artifact to `.clutch/renders/<stem>/a<i>/cand-<k>.<ext>` in its own worktree. `<i>` is the zero-based position of the artifact in the ticket's `## Render` block, and `<k>` is the zero-based candidate index. `.clutch/` is gitignored, so candidates are never committed, and Implement never writes an artifact path. Check reads the same paths from the worktree and copies the candidates and their operator images into the attempt spool render directory, the same `<spool root>/<stem>/<attempt>/render/` that `check_render` writes, under the same `a<i>/` subdirectory.

(b) For each artifact, Check runs the layer-1 `image_quality` judgment on every candidate and drops any that fails a hard check. It then runs the `review_visual` judge from `clutch/visual.py` on each survivor, with the rubric rows for that artifact (the `visual:` criteria that name it, plus the fixed generate-mode rows).

(c) Layer-1 scores: `clutch/images.py` gains a `scores` function returning the preservation SSIM and the total ORB match count that `judge` already computes. `judge` and `scores` share the same two helpers, so the numbers are computed one way.

(d) Ranking is a pure function in `clutch/visual.py`, applied to one artifact's candidates: judge overall verdict (`accept` before `unsure` before `reject`), then the count of `pass` rows, then the layer-1 preservation score, then the presence score.

(e) Select commit: for each artifact, the top candidate whose verdict is `accept` and which has a margin (at least one more `pass` row than the runner-up, or is the only survivor) is the selected one. Only when every declared artifact has a selected candidate does Check copy each selected candidate to its artifact path and make one commit titled `clutch(<stem>): select`. The commit body has one line per artifact, `<artifact path>: candidate <k>, evidence <id>`, naming the selected candidate index and the judge call's evidence id (plan open decision 3, Proposed option).

(f) Park: if any one artifact has no `accept`, an `accept` without margin, any `unsure` overall verdict, or zero survivors, Check fails the whole ticket with a finding whose code is `visual_undecided`, names the undecided artifact path(s), and makes no select commit, not even for artifacts that were decided. The side-by-side and heatmap images for each survivor stay in the attempt render directory.

(g) Release: a Check failure with finding code `visual_undecided` becomes the terminal reason through `failure_terminal` (clutch/runner.py). The drain re-offers a non-premise parked stem under the `retry` cap (`reofferable` and `record_reoffer` in clutch/drain.py), and Implement then writes fresh candidates for every artifact. No person is involved in the release and no new verb is named. When the `attempts` cap is spent, the existing escalation applies and routes to `reject_queue` with verdict `abandon-human`. That is the generic terminal every spent cap takes, not a release of this park. Plan open decision 4 has no Proposed option and its AI design panel record is not in this repo. If a panel later records a different release, that is a separate ticket.

The single select commit lets the correctness review see every committed image while the visual judgment is already on record.

## Boundary contract
### Graphics candidate selection
- disposition: create
- owner: clutch/visual.py (ranking and margin decision, pure); clutch/stages.py (candidate collection, select commit, park finding)
- consumers: Check stage for graphics tickets in generate mode; the correctness review, which reads the select commit; `failure_terminal` and the drain re-offer, which carry `visual_undecided`
- observable change: generate-mode graphics tickets commit one selected image per declared artifact in one select commit, or fail Check with `visual_undecided` and commit nothing; Implement writes candidates under `.clutch/renders/<stem>/a<i>/` and never an artifact path
- compatibility: a ticket declaring one artifact behaves as a one-artifact case of the same flow; command-mode graphics and non-graphics tickets are unchanged; `parse_render` and the `review_visual` reply schema and `judge_samples` majority are reused unchanged; `images.judge` keeps its signature and results
- acceptance: per-artifact candidate paths, ranking order, margin rule, all-or-nothing select commit, commit message, park finding code and the re-offer are each decided by tests
- tests: new unit tests for ranking, margin and the stages selection flow with fakes, including a two-artifact ticket; new integration test with a real repo
- post-merge source of truth: clutch/visual.py for ranking; clutch/stages.py for the select and park flow
- closest existing: `visual.majority` and `visual.parse_reply` (per-row verdicts for one candidate), `images.judge` (failure strings only), and the Check autofix commit path in `clutch/stages.py`; none ranks several candidates, decides a margin, or exposes scores
- earning reason: ranking and margin are consumed by both the select commit and the park decision and need a pure, testable owner outside the stage code

### Layer-1 scores
- disposition: extend
- owner: clutch/images.py
- consumers: the candidate ranking in Check, and the `{{scores}}` input of the `review_visual` spec
- observable change: a new `scores(artifact, inputs)` returns the preservation SSIM and total ORB match count
- compatibility: `judge`, its thresholds and its failure strings are preserved byte for byte
- acceptance: `scores` returns the numbers `judge` compares to `MIN_SSIM` and `MIN_ORB_MATCHES`
- tests: new unit test with a fake loader seam
- post-merge source of truth: clutch/images.py

## Scope in / Scope out
Scope in:
- In `clutch/images.py`, extract the SSIM and ORB-match computations of `judge` into two private helpers, have `judge` call them, and add `scores(artifact, inputs)` returning `(ssim, orb_matches)`, with `None` for a value whose input kind is absent. Nothing else in the file changes.
- Add a pure `rank` and `decide` pair to `clutch/visual.py`. Inputs are one artifact's per-candidate overall verdict, `pass` row count and layer-1 scores. Output is the selected index, or `None` with reason `visual_undecided`. The caller applies it once per declared artifact.
- In `clutch/stages.py`, add one function for Check on generate-mode graphics tickets. For each declared artifact in order it collects `cand-<k>.<ext>` from `.clutch/renders/<stem>/a<i>/` in the worktree, copies them to the spool render directory, drops candidates failing `images.judge`, calls the judge per survivor and calls `decide`. If every artifact is decided it copies each selected candidate to its artifact path and makes the single select commit; otherwise it returns one `visual_undecided` finding naming the undecided artifact paths and makes no commit. On a park, `check()` returns `refused([visual_undecided finding], Cost(seconds=active_seconds()))` at once, before `gather_evidence` and `run_gates`, with no `checks.json`, so the only finding code is `visual_undecided` and `failure_terminal` joins it to exactly that reason (the gates would otherwise add a `verification` finding for the empty branch). Wire it in `check()` before `gather_evidence`, as `check_autofix` is, so the select commit exists when Verification runs and the gates read `changed_files`; in generate mode Implement itself commits nothing. Each judge call goes through `driver.run` with its own `key_scope` (`a<i>c<k>s<j>` for artifact `i`, candidate `k`, sample `j`, matching `[a-z][a-z0-9]*`), because `call_seq` restarts at 1 on every run and an unscoped repeat reuses one effect key and replays the first reply (`clutch/llmeffect.py::scoped_seq`). The judge call's evidence id in the select commit body is that call's effect key, recomputed in stage code as `llm_key(stem, scoped_seq(scope, journal_run_seq(ctx.driver.journal.read(), stem)), "review_visual", attempt, call_seq)` where `call_seq` is the `StageResult.cost.attempts` of that judge call (the last call it made, so a re-prompt after an invalid reply names the accepted call, not the first), and the commit body names the key of sample `s0` of the winning candidate's judge call for each artifact (the first sample's accepted call) with `llm_key` and `scoped_seq` from `clutch.llmeffect` and `journal_run_seq` imported as `from clutch.journal import run_seq as journal_run_seq`; the evidence store's `#n` suffix is not used. Before selecting, the function checks the branch diff against main: if it already changes any declared artifact path or any `.clutch/renders/` path, it returns a hard finding with a paved road (Implement writes candidates only under `.clutch/renders/<stem>/a<i>/` and never an artifact path) and makes no select commit. Image decoding and git go through the existing seams, so a fenced unit test can run these lines with fakes.
- In `clutch/specs/implement.md`, edit only the existing graphics paragraph, to give the per-artifact candidate path `.clutch/renders/<stem>/a<i>/cand-<k>.<ext>` and say no artifact path is ever written by Implement. Bump the spec `version` to the next minor above the version on main (no literal target is written here). Update the pins that force an edit: the implement version pins in `tests/unit/test_specs.py`, `tests/integration/test_specs_delimiter_note.py` and `tests/integration/test_implement_spec_mutation_check.py`, and the `spec: implement` version assertion in `tests/integration/test_stages.py`. Those pin edits are the only expected changes in those four files.
- In `docs/how-clutch-works.md`, update only the section that describes Check for graphics tickets, to describe per-artifact candidates, the single select commit and the `visual_undecided` finding.

Scope out:
- Any change to `clutch/tickets.py` or `parse_render`: several artifacts stay allowed.
- The `visual_baseline` GO verdict and `eval/visual/` (`visual-review-baseline`).
- Any new CLI verb or config key, and any change to `clutch/drain.py` or `clutch/runner.py`; the re-offer uses the existing machinery.
- Command-mode graphics.
- Changes to the judge rubric or reply schema.
- Moving the judge onto the `majority-verdict` combiner of the stage-panels plan.

## Scope fence
- clutch/images.py
- clutch/visual.py
- clutch/stages.py
- clutch/specs/implement.md
- docs/how-clutch-works.md
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_implement_spec_mutation_check.py
- tests/integration/test_stages.py
- tests/unit/test_visual_select.py
- tests/unit/test_images_scores.py
- tests/unit/test_stages_candidates_select.py
- tests/integration/test_image_candidates_select.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_visual_select.py` shows `decide` returns the index of an `accept` candidate with more `pass` rows than the runner-up, and returns `None` with reason `visual_undecided` when two `accept` candidates tie on `pass` rows, not the first index.
2. `./dev.py test tests/unit/test_visual_select.py` shows an `unsure` overall verdict on any survivor yields `None`, not a selection of another `accept`. It also shows a single `accept` survivor is selected without margin, and an empty survivor list returns `None`.
3. `./dev.py test tests/unit/test_visual_select.py` shows ranking orders `accept` above `unsure` above `reject`, then by `pass` count, then by preservation score, then by presence score, with a fixed input whose preservation score alone decides the order.
4. `./dev.py test tests/unit/test_images_scores.py tests/unit/test_images_checks.py` shows `scores` returns the SSIM and ORB match count that `judge` compares to its thresholds, and `judge` returns the same failure strings as before the refactor.
5. `./dev.py test tests/unit/test_stages_candidates_select.py` shows, with fake fs, git, driver seams and in-memory judge replies, for a ticket declaring one artifact, that the new stages function drops a candidate failing `images.judge`, makes exactly one `clutch(<stem>): select` commit whose body names the candidate index and judge evidence id for the artifact, and returns a `visual_undecided` finding with no commit for a tie, an `unsure` verdict, and zero survivors.
6. `./dev.py test tests/unit/test_stages_candidates_select.py` shows two survivors given different judge replies through the driver's effect layer receive different verdicts (each `driver.run` call carries a distinct `key_scope`), and that the evidence id in the select commit equals the scoped `llm_key` of the winning candidate's judge call, not a guessed or unscoped key; and in a fixture where the first judge reply is invalid and re-prompted, the id ends in `/2`, the accepted call, not `/1`.
7. `./dev.py test tests/unit/test_stages_candidates_select.py` shows, for a ticket declaring two artifacts, that candidates are read from `.clutch/renders/<stem>/a0/` and `.clutch/renders/<stem>/a1/` separately, that each artifact is ranked only among its own candidates, and that when both are decided exactly one select commit is made whose body has one line per artifact path with its own candidate index and evidence id, not one shared index.
8. `./dev.py test tests/unit/test_stages_candidates_select.py` shows that when artifact `a0` has a clear winner and artifact `a1` is undecided, the function returns a `visual_undecided` finding naming the `a1` artifact path and makes no commit at all, not a commit for `a0` alone.
9. `./dev.py test tests/integration/test_image_candidates_select.py` shows a Check run in a real repo with three candidates for one artifact under `.clutch/renders/<stem>/a0/`, one failing a hard check, makes exactly one commit titled `clutch(<stem>): select`. The artifact path holds that candidate's bytes and no `cand-*` file is in the commit. An undecided run makes no commit touching any artifact path, and the side-by-side and heatmap files for each survivor exist in the spool render directory.
10. `./dev.py test tests/integration/test_image_candidates_select.py` drives a real undecided Check (not a hand-built finding list) through `failure_terminal` and asserts `reason == "visual_undecided"` exactly, with no `verification` code; that failure is is re-offered by the drain under the `retry` cap via `reofferable`, and when the `attempts` cap is spent takes the `reject_queue` route rather than looping.
11. `./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_mutation_check.py tests/integration/test_stages.py` passes with the implement spec at the bumped version, and `git diff main -- clutch/specs/implement.md` shows only the graphics paragraph and the version line changed.
12. `./dev.py test tests/unit/test_visual_review.py tests/integration/test_visual_review_spec.py` still passes, which shows the judge schema and `judge_samples` majority are unchanged.
13. `./dev.py test tests/unit/test_stages_candidates_select.py tests/integration/test_image_candidates_select.py` shows that when the branch diff against main, before selection, already changes any declared artifact path or any `.clutch/renders/` path, the function returns a hard finding with a paved road and makes no select commit, not a commit that overwrites the path.
14. `./dev.py test tests/integration/test_image_candidates_select.py` shows that for a clear-winner Check run, `checks.json` lists the artifact path in `changed_files` and the `verification` report passes, so the select commit was visible to Verification and the gates.

## Verification
```
./dev.py test tests/unit/test_visual_select.py tests/unit/test_images_scores.py tests/unit/test_images_checks.py tests/unit/test_stages_candidates_select.py tests/integration/test_image_candidates_select.py tests/unit/test_visual_review.py tests/integration/test_visual_review_spec.py tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_mutation_check.py tests/integration/test_stages.py
```

## Definition of rejected
The branch is thrown away if Implement can still commit a candidate or write an artifact path directly in generate mode. It is also thrown away if a tie, an `unsure` verdict or zero survivors on any artifact selects a candidate, if a partly decided ticket commits any artifact, if two artifacts share one candidate path or one selected index, if the re-offer of a `visual_undecided` park needs a person, if `images.judge` results change, or if a verb, config key or fallback that no code implements is named anywhere.

## Time budget
- expected: 30m
- stuck: 60m
- reason: the pure ranking, the score function, the per-artifact Check wiring and the re-offer test share one decision flow and one test rig. Splitting would leave a park with no release, which the engine rules forbid.
