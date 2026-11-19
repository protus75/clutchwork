---
state: draft
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- graphics-render-check
- route-kinds-filter-r1
- image-quality-gate-r1

## Context
- docs/gemini-graphics-refactor-plan.md#B5. Layer 2: the vision-model judge (`visual-review-surface`)
- clutch/specs/__init__.py::ENGINE_LLM_SURFACES
- clutch/config.py::Config
- clutch/observe.py
- clutch/artifacts.py

## Goal / Why
Roadmap row 53, Layer 2 of the graphics grading. Today no prompt spec, reply schema or config knob exists for judging a rendered or generated image. After this ticket: (a) `review_visual` is a member of the closed surface vocabulary and ships a spec `clutch/specs/review_visual.md` (read-only, JSON reply) carrying the rubric; (b) a new pure module `clutch/visual.py` owns the reply schema, its validation against the rubric rows, and the per-row majority combiner; (c) config gains `graphics.judge_samples` (integer 1 to 3, default 1).

Rubric: the ticket's `visual:` criteria, plus for `mode: generate` five fixed rows with stable ids: `identity` (input present and recognisable, same identity and proportions), `placement` (requested position and scale), `lighting` (lighting, shadows and perspective match the base), `unchanged` (everything outside the insert region unchanged), `artifacts` (no warped text, extra limbs, seams or duplicated objects).

Reply schema: one `pass`, `fail` or `unsure` per rubric row with the observation that decided it, and an overall verdict `accept`, `reject` or `unsure` with one sentence of reason. A reply that skips a row, repeats a row, or names a row outside the rubric is refused with a paved road, so the driver can re-prompt as it does for every reply.

Majority: given `judge_samples` valid replies, each row takes the strict majority verdict across samples and the overall verdict takes the strict majority overall verdict; a tie, including any split with no strict majority, is `unsure`. One sample returns that reply unchanged.

This ticket does not call the judge from any stage and does not change routing; it delivers the spec, the schema and the combiner those calls use.

## Boundary contract
### Surface vocabulary and spec
- disposition: extend
- owner: clutch/specs/__init__.py
- consumers: spec loader and lint, `clutch/observe.py` step names, `clutch/help.py`, the extension step icons, `providers.resolve` callers that already name `review_visual`
- observable change: `ENGINE_LLM_SURFACES` gains `review_visual`; `clutch/specs/review_visual.md` (version `1.0`, `llm_surface: review_visual`, read-only) lints clean; `STEP_NAMES` has a `review_visual` key with step kinds, a help entry and an icon
- compatibility: every existing surface and spec is unchanged; `WRITING_SURFACES` does not gain the surface, so the judge stays read-only
- acceptance: spec lint passes and every member of `ENGINE_LLM_SURFACES` has a `STEP_NAMES` key
- tests: `tests/integration/test_visual_review_spec.py`, `tests/unit/test_step_names_cover_surfaces.py`, `tests/integration/test_closed_sets.py`
- post-merge source of truth: clutch/specs/__init__.py

### Judge reply schema and majority
- disposition: create
- owner: clutch/visual.py
- consumers: the candidate-selection and baseline work that reads judge verdicts (two production consumers beyond this ticket's tests)
- observable change: `rubric_ids(visual_criteria, mode)`, `parse_reply(text, row_ids)` and `majority(replies)` exist; invalid replies raise `ValueError` naming the defect and the road
- compatibility: new module, nothing imports it yet outside tests
- acceptance: the criteria below
- tests: `tests/unit/test_visual_review.py`
- post-merge source of truth: clutch/visual.py
- closest existing: `clutch/artifacts.py` reply validators and `clutch/requisition.py` verdict parsing; both validate a different closed vocabulary (approve/snag findings) with no per-row verdicts or sample combiner, so neither can be reused
- earning reason: more than one production consumer needs one shared owner for the schema and the majority rule, so each stage does not carry its own copy

### Config graphics section
- disposition: extend
- owner: clutch/config.py
- consumers: the future judge caller; `clutch/docs/host-contract.md` field inventory
- observable change: `Config.graphics.judge_samples`, integer 1 to 3, default 1; a value outside 1..3 or an unknown key under `graphics` is refused by the strict loader
- compatibility: the key is optional and additive, so `schema_version` stays 1 and existing configs load unchanged
- acceptance: defaults and refusals pinned by the criteria below
- tests: `tests/unit/test_visual_review.py`
- post-merge source of truth: clutch/config.py

## Scope in / Scope out
In:
- `clutch/specs/review_visual.md`: new spec with the five standard sections, inputs as data blocks (ticket, generator prompt, input and reference images, candidate artifacts, layer-1 scores, rubric), the JSON reply rules and the required first-character sentence. Judge-from-a-different-family is already enforced by route lint and is not repeated.
- `clutch/visual.py`: new, pure (no I/O, no clock, no model call).
- `clutch/specs/__init__.py`: `ENGINE_LLM_SURFACES` gains `review_visual`; nothing else.
- `clutch/observe.py`: `STEP_NAMES` gains `review_visual` and the derived step kinds follow.
- `clutch/help.py`: the `step` topic entries the new kinds need, and any vocabulary entry the help tests then require.
- `vscode-clutchwork/extension.js`: the icon lookup entries the new step kinds need, by lookup table only.
- `clutch/config.py`: new `Graphics` model and `Config.graphics` field.
- `clutch/docs/host-contract.md`: add `graphics.judge_samples` to the config field inventory only.
- `tests/integration/test_closed_sets.py`: the `ENGINE_LLM_SURFACES` pin gains `review_visual`; no other assertion changes.
- `tests/integration/test_visual_review_spec.py`: new; holds the one test that loads the repo spec file.
- Any existing test that pins the whole serialized `Config` or the full surface list and fails for exactly these additions may change only that expectation, and only if it is listed in the fence.

Out: calling the judge from any stage, routing changes, Check or Implement spec changes, the `review.md` spec, layer-1 gate code, calibration fixtures, and `docs/roadmap.md`.

## Scope fence
- clutch/specs/review_visual.md
- clutch/specs/__init__.py
- clutch/visual.py
- clutch/config.py
- clutch/observe.py
- clutch/help.py
- clutch/docs/host-contract.md
- vscode-clutchwork/extension.js
- tests/integration/test_closed_sets.py
- tests/integration/test_visual_review_spec.py
- tests/unit/test_visual_review.py

## Acceptance criteria
1. `tests/integration/test_visual_review_spec.py::test_spec_lints` loads `clutch/specs/review_visual.md` through `load_spec` and gets `llm_surface == "review_visual"` and `version == "1.0"`; a spec with any other surface name is refused, not accepted. Check: `./dev.py test tests/integration/test_visual_review_spec.py`.
2. `tests/unit/test_visual_review.py::test_rubric_ids` asserts `rubric_ids(["a"], "generate")` is `["a", "identity", "placement", "lighting", "unchanged", "artifacts"]` and `rubric_ids(["a"], "command")` is `["a"]`, not the five fixed rows. Check: `./dev.py test tests/unit/test_visual_review.py`.
3. `tests/unit/test_visual_review.py::test_parse_reply_refusals` asserts `parse_reply` raises `ValueError` for a reply that skips a rubric row, one that repeats a row, one that names a row not in the rubric, and one whose overall verdict is `maybe`; and returns a parsed reply (not an exception) for a complete valid reply. Check: `./dev.py test tests/unit/test_visual_review.py`.
4. `tests/unit/test_visual_review.py::test_majority` asserts with three samples that rows split 2-1 take the majority verdict, that a 1-1-1 split yields `unsure`, that with two samples a 1-1 split yields `unsure`, and that one sample is returned unchanged; the overall verdict follows the same rule. Check: `./dev.py test tests/unit/test_visual_review.py`.
5. `tests/unit/test_visual_review.py::test_judge_samples_config` asserts `Config.graphics.judge_samples` defaults to `1`, accepts `3`, and that `0`, `4` and an unknown key under `graphics` each raise a validation error, not load. Check: `./dev.py test tests/unit/test_visual_review.py`.
6. `"review_visual" in ENGINE_LLM_SURFACES`, `"review_visual" not in providers.WRITING_SURFACES`, and every member of `ENGINE_LLM_SURFACES` is a key of `STEP_NAMES`. Check: `./dev.py test tests/unit/test_step_names_cover_surfaces.py tests/integration/test_closed_sets.py`.
7. The help and step-icon tests report no missing entry for the new step kinds. Check: `./dev.py test tests/unit/test_help.py tests/integration/test_help.py tests/integration/test_step_icons.py`.

## Verification
```
./dev.py test tests/unit/test_visual_review.py tests/integration/test_visual_review_spec.py tests/unit/test_step_names_cover_surfaces.py tests/integration/test_closed_sets.py tests/unit/test_help.py tests/integration/test_help.py tests/integration/test_step_icons.py tests/unit/test_specs.py tests/integration/test_specs_json_reply_specs.py tests/integration/test_host_contract.py tests/integration/test_config.py
```

## Definition of rejected
- `review_visual` is added to `WRITING_SURFACES`, or the spec grants write tools.
- `clutch/visual.py` performs I/O, reads a clock or calls a model.
- A stage, router or Check path starts calling the judge in this ticket.
- A tie in the majority resolves to `pass`, `accept` or `fail`/`reject` instead of `unsure`.
- Extension JavaScript derives a step name or icon by logic rather than a lookup entry.

## Time budget
- expected: 25m
- stuck: 50m
- reason: one new spec, one small pure module and three registry additions that share one surface name; splitting would leave a surface with no spec or a spec with no registered surface.
