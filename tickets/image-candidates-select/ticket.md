---
state: draft
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
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
Roadmap row 54, Gemini plan B6 (Layer 3). Today Implement writes the artifact path directly on a `kind: graphics` ticket in `mode: generate`, and nothing ranks candidates, selects one, or parks an undecidable result. After this ticket:

(a) In `generate` mode Implement writes `candidates:` images (default 3) to `.clutch/renders/<stem>/cand-<k>.<ext>` in its own worktree. `.clutch/` is gitignored, so candidates are never committed, and Implement does not write the artifact path. The path is fixed, so the implement spec's graphics paragraph names it and Check reads the same path from the worktree. Check copies the candidates and their operator images into the attempt spool render directory, the same `<spool root>/<stem>/<attempt>/render/` that `check_render` writes.

(b) Check runs the layer-1 `image_quality` judgment on every candidate and drops any that fails a hard check. It then runs the `review_visual` judge from `clutch/visual.py` on each survivor.

(c) Layer-1 scores: `clutch/images.py` gains a `scores` function returning the preservation SSIM and the total ORB match count that `judge` already computes. `judge` and `scores` share the same two helpers, so the numbers are computed one way.

(d) Ranking is a pure function in `clutch/visual.py`: judge overall verdict (`accept` before `unsure` before `reject`), then the count of `pass` rows, then the layer-1 preservation score, then the presence score.

(e) Select commit: the top candidate whose verdict is `accept` and which has a margin (at least one more `pass` row than the runner-up, or is the only survivor) is copied to the artifact path and committed as `clutch(<stem>): select`. The commit message names the candidate index and the judge call's evidence id (plan open decision 3, Proposed option).

(f) Park: no `accept`, an `accept` without margin, any `unsure` overall verdict, or zero survivors makes Check fail with a finding whose code is `visual_undecided`. The side-by-side and heatmap images for each survivor stay in the attempt render directory.

(g) Release: a Check failure with finding code `visual_undecided` becomes the terminal reason through `failure_terminal` (clutch/runner.py). The drain re-offers a non-premise parked stem under the `retry` cap (`reofferable` and `record_reoffer` in clutch/drain.py), and Implement then writes fresh candidates. No person is involved in the release and no new verb is named. When the `attempts` cap is spent, the existing escalation applies and routes to `reject_queue` with verdict `abandon-human`. That is the generic terminal every spent cap takes, not a release of this park. The "no person" clause covers the release (the re-offer), not the cap escalation. Plan open decision 4 has no Proposed option and its AI design panel record is not in this repo. If a panel later records a different release, that is a separate ticket.

The single select commit lets the correctness review see the committed image while the visual judgment is already on record.

## Boundary contract
### Graphics candidate selection
- disposition: create
- owner: clutch/visual.py (ranking and margin decision, pure); clutch/stages.py (candidate collection, select commit, park finding)
- consumers: Check stage for graphics tickets in generate mode; the correctness review, which reads the select commit; `failure_terminal` and the drain re-offer, which carry `visual_undecided`
- observable change: generate-mode graphics tickets commit one selected image or fail Check with `visual_undecided`; Implement writes candidates under `.clutch/renders/<stem>/` and never the artifact path
- compatibility: command-mode graphics and non-graphics tickets are unchanged; the `review_visual` reply schema and `judge_samples` majority are reused unchanged; `images.judge` keeps its signature and results
- acceptance: ranking order, margin rule, select commit message, park finding code and the re-offer are each decided by tests
- tests: new unit tests for ranking, margin and the stages selection flow with fakes; new integration test with a real repo
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
- Add a pure `rank` and `decide` pair to `clutch/visual.py`. Inputs are per-candidate overall verdict, `pass` row count and layer-1 scores. Output is the selected index, or `None` with reason `visual_undecided`.
- In `clutch/stages.py`, add one function for Check on generate-mode graphics tickets. It collects `cand-<k>.<ext>` from `.clutch/renders/<stem>/` in the worktree, copies them to the spool render directory, drops candidates failing `images.judge`, calls the judge per survivor, calls `decide`, then makes the select commit or returns a `visual_undecided` finding. Wire it where `check_render` is called. Image decoding and git go through the existing seams, so a fenced unit test can run these lines with fakes.
- In `clutch/specs/implement.md`, edit only the existing graphics paragraph, to give the candidate path `.clutch/renders/<stem>/cand-<k>.<ext>` and say the artifact path is never written by Implement. Bump the spec `version` to the next minor above the version on main (no literal target is written here). Update the pins that force an edit: line 25 and line 129 of `tests/unit/test_specs.py`, line 14 of `tests/integration/test_specs_delimiter_note.py`, line 14 of `tests/integration/test_implement_spec_mutation_check.py`, and the `spec: implement 2.19` assertion at line 341 of `tests/integration/test_stages.py`. Those pin edits are the only expected changes in those four files.
- In `docs/how-clutch-works.md`, update only the section that describes Check for graphics tickets, to describe selection, the select commit and the `visual_undecided` finding.

Scope out:
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
5. `./dev.py test tests/unit/test_stages_candidates_select.py` shows, with fake fs, git, driver seams and in-memory judge replies, that the new stages function drops a candidate failing `images.judge`, makes exactly one `clutch(<stem>): select` commit naming the candidate index and judge evidence id for a clear winner, and returns a `visual_undecided` finding with no commit for a tie, an `unsure` verdict, and zero survivors.
6. `./dev.py test tests/integration/test_image_candidates_select.py` shows a Check run in a real repo with three candidates under `.clutch/renders/<stem>/`, one failing a hard check, makes exactly one commit titled `clutch(<stem>): select`. The artifact path holds that candidate's bytes and no `cand-*` file is in the commit. An undecided run makes no commit touching the artifact path, and the side-by-side and heatmap files for each survivor exist in the spool render directory.
7. `./dev.py test tests/integration/test_image_candidates_select.py` shows a Check failure with finding code `visual_undecided` is the terminal reason from `failure_terminal`, is re-offered by the drain under the `retry` cap via `reofferable`, and when the `attempts` cap is spent takes the `reject_queue` route rather than looping.
8. `./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_mutation_check.py tests/integration/test_stages.py` passes with the implement spec at the bumped version, and `git diff main -- clutch/specs/implement.md` shows only the graphics paragraph and the version line changed.
9. `./dev.py test tests/unit/test_visual_review.py tests/integration/test_visual_review_spec.py` still passes, which shows the judge schema and `judge_samples` majority are unchanged.

## Verification
```
./dev.py test tests/unit/test_visual_select.py tests/unit/test_images_scores.py tests/unit/test_images_checks.py tests/unit/test_stages_candidates_select.py tests/integration/test_image_candidates_select.py tests/unit/test_visual_review.py tests/integration/test_visual_review_spec.py tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_mutation_check.py tests/integration/test_stages.py
```

## Definition of rejected
The branch is thrown away if Implement can still commit a candidate or write the artifact path directly in generate mode. It is also thrown away if a tie, an `unsure` verdict or zero survivors selects a candidate, if the re-offer of a `visual_undecided` park needs a person, if `images.judge` results change, or if a verb, config key or fallback that no code implements is named anywhere.

## Time budget
- expected: 30m
- stuck: 60m
- reason: the pure ranking, the score function, the Check wiring and the re-offer test share one decision flow and one test rig. Splitting would leave a park with no release, which the engine rules forbid.
