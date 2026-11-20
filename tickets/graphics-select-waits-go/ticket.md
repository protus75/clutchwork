---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- image-candidates-select-r1
- visual-review-baseline

## Context
- clutch/baseline.py
- clutch/policy.py::visual_identity
- clutch/stages.py::check_candidates
- eval/visual_harness.py::run_baseline
- tests/unit/test_stages_candidates_select.py
- tests/integration/test_image_candidates_select.py
- docs/how-clutch-works.md#4.3 Check
- docs/how-clutch-works.md#9.6 Scorecard and baseline

## Goal / Why
Roadmap row 169; Gemini graphics plan B7 and roadmap decision 17 say every graphics ticket parks until a `visual_baseline` GO is recorded for the current judge. Today `check_candidates` in `clutch/stages.py` judges candidates and commits `clutch(<stem>): select` without reading that signal, so an unmeasured, NO_GO, or stale-routing judge selects images. After this ticket, Check for a graphics `generate` ticket returns the existing `visual_undecided` finding, before any judge call or select commit, unless the journal's latest `visual_baseline` signal is GO and its recorded identity equals the current `policy.visual_identity(config, specs_dir)` (same routing rows per tier and `review_visual` spec major). A judge route or spec-major change therefore revokes GO, as the review baseline's does. The park is the one B6 already defines (`visual_undecided`, re-offered and spent by the existing caps path); this ticket adds no new finding code, hold, or verb.

## Boundary contract
### Visual baseline binding reader
- disposition: extend
- owner: clutch/baseline.py
- consumers: `check_candidates` in clutch/stages.py (the only reader of the `visual_baseline` signal besides its writer, eval/visual_harness.py)
- observable change: new `resolve_visual_baseline(config, events, *, specs_dir)` returns the existing `BaselineResolution` (ABSENT, NO_GO, GO, REVOKED). The latest `visual_baseline` signal decides: no signal is ABSENT, verdict other than GO is NO_GO, GO whose `identity` differs from `visual_identity(config, specs_dir)` is REVOKED, an event of unknown type or non-mapping body, or any exception while reading or comparing, is REVOKED. Only GO binds.
- compatibility: `resolve_baseline` and the `review_baseline` signal are untouched; the signal body the harness writes is read as written, unchanged.
- acceptance: unit test per state, including a stale identity and a malformed event, each asserting not-GO
- tests: tests/unit/test_baseline_visual.py
- post-merge source of truth: clutch/baseline.py

### Check candidate selection
- disposition: extend
- owner: clutch/stages.py::check_candidates
- consumers: `check` in clutch/stages.py, the drain's re-offer and attempts accounting for `visual_undecided`
- observable change: after the `candidate_paths` refusal and before any judge call, a non-GO resolution returns one `Finding(code="visual_undecided")` whose message says the visual_baseline GO is missing or stale and whose paved road names no launcher or verb: the ticket stays parked until a GO `visual_baseline` is recorded for the current `review_visual` routing and spec major, then retry. The release already exists and is merged (the visual baseline harness from `visual-review-baseline`, fed by the fixtures of the roadmap row `visual-baseline-fixtures`); it is the engine's own measurement, not a host action, and the owner decided no new verb for it. No candidate is judged, nothing is written to the artifact path, and no select commit is made. With GO, behavior is unchanged.
- compatibility: `candidate_paths` check order, select commit message, and the GO path are preserved; non-graphics and `command` tickets return `[]` before the baseline is read.
- acceptance: park without GO, select with GO, no judge call and no commit when parked
- tests: tests/unit/test_stages_candidates_select.py, tests/integration/test_image_candidates_select.py
- post-merge source of truth: clutch/stages.py and docs/how-clutch-works.md section 4.3

## Scope in / Scope out
Scope in:
- `clutch/baseline.py`: add `resolve_visual_baseline` beside `resolve_baseline`, importing `VISUAL_BASELINE_SIGNAL` and `visual_identity` from `clutch/policy.py`; reuse `BaselineResolution`. Compare the whole recorded identity to the current one by equality.
- `clutch/stages.py`: in `check_candidates`, after the `candidate_paths` return and before building `inputs`, call `resolve_visual_baseline(ctx.config, ctx.driver.journal.read(), specs_dir=ctx.specs_dir)`; when it does not bind, return the `visual_undecided` finding described above. Import it at module top (`import clutch.baseline, clutch.stages` already loads together).
- `tests/unit/test_baseline_visual.py` (new): the reader's states.
- `tests/unit/test_stages_candidates_select.py`: its `fixture` makes the selecting tests reach the GO path by monkeypatching `stages.resolve_visual_baseline` to return `BaselineResolution("GO")`, and adds only `specs_dir=None` to its `ctx` SimpleNamespace (the one attribute the change newly reads that the stand-in lacks). Add one test: a non-GO resolution returns `visual_undecided`, never calls `ctx.driver.run`, writes nothing, and makes no commit.
- `tests/integration/test_image_candidates_select.py`: `rig` appends one GO `visual_baseline` signal (body `signal`, `verdict`, `identity` from `visual_identity(config, SPECS)`, `overall`, `case_count`) to the driver journal so the existing selecting tests keep selecting; because `visual_identity` resolves `review_visual` for every tier and the shared `CONFIG` in `tests/integration/test_stages.py` (left untouched) routes only tier medium, `rig` rewrites the repo's `config.yaml` text before `load_config` to add a `review_visual` routing row for tiers low, high and max beside the existing rows, so every tier resolves. Also add one test that a journal without the signal parks with no select commit; no other change to that file.
- `docs/how-clutch-works.md`: section 4.3 item 2 states that Check returns `visual_undecided` before judging unless the latest `visual_baseline` is GO for the current judge routing and spec major; section 9.6's visual baseline bullet adds that Check reads it. Nothing else in that file changes.

Scope out: no new verb, journal event, config knob, finding code, or recurring test or gate; no change to `eval/visual_harness.py` (the writer), `clutch/policy.py`, `clutch/journal.py`, or `clutch/specs/*` (no spec version bump, so no spec test pin); no release or parking mechanism beyond the existing `visual_undecided` path; no docs outside `docs/how-clutch-works.md`; the roadmap and the plan are not edited. A graphics ticket parked before GO spends the existing retry and attempts caps like any `visual_undecided`; changing that is a different ticket.

## Scope fence
- clutch/baseline.py
- clutch/stages.py
- tests/unit/test_baseline_visual.py
- tests/unit/test_stages_candidates_select.py
- tests/integration/test_image_candidates_select.py
- docs/how-clutch-works.md

## Acceptance criteria
1. `resolve_visual_baseline` returns state GO with `binds` true for a latest `visual_baseline` GO whose identity equals the current identity, and returns ABSENT for no signal, NO_GO for a NO_GO verdict, and REVOKED for a GO whose identity differs (changed model or `spec_major`), never GO for any of them; checked by `./dev.py test tests/unit/test_baseline_visual.py`.
2. A GO followed by a later NO_GO signal resolves NO_GO, not GO, and a malformed event (non-mapping body) resolves REVOKED without raising; checked by `./dev.py test tests/unit/test_baseline_visual.py`.
3. `check_candidates` with a non-GO resolution returns `[Finding(code="visual_undecided")]`, makes zero `ctx.driver.run` calls, writes no artifact, and makes zero `ctx.git.commit` calls, not a select commit; checked by `./dev.py test tests/unit/test_stages_candidates_select.py`.
4. `check_candidates` with GO still selects and commits `clutch(<stem>): select` as before, and the `candidate_paths` refusal still fires before the baseline is read; checked by `./dev.py test tests/unit/test_stages_candidates_select.py tests/integration/test_image_candidates_select.py`.
5. With a real journal holding no `visual_baseline` signal, `stages.check` returns `visual_undecided` and the ticket branch head is unchanged (no select commit); with the GO signal recorded it selects; checked by `./dev.py test tests/integration/test_image_candidates_select.py`.
6. `docs/how-clutch-works.md` section 4.3 item 2 and section 9.6 describe the baseline read; one-time review check, not a standing test.

## Verification
```
./dev.py test tests/unit/test_baseline_visual.py tests/unit/test_stages_candidates_select.py tests/integration/test_image_candidates_select.py
```

## Definition of rejected
The branch is rejected if a graphics `generate` ticket can still commit a select commit with no GO, a NO_GO, or a stale-identity `visual_baseline`; if a new verb, journal event, config knob, or finding code is added; if Check judges candidates before reading the baseline; or if any file outside the fence changes.

## Time budget
- expected: 14m
- stuck: 28m
