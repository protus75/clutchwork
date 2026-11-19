---
state: draft
source: human
priority: P1
kind: feature
---

## Depends on
- boundary-contract-implementation-review

## Context
- docs/gemini-graphics-refactor-plan.md#B8. Spec updates
- clutch/docs/host-authoring.md#Graphics tickets

## On-demand
- clutch/specs/requisition_review.md
- clutch/specs/review.md

## Goal / Why
Roadmap row 171, gemini-graphics-refactor-plan B8. Neither `clutch/specs/requisition_review.md` nor `clutch/specs/review.md` mentions graphics today, though graphics tickets (`kind: graphics`, `## Render`, `visual:` criteria, the `clutch(<stem>): select` commit written by Check) are merged. After this ticket: (1) the requisition reviewer snags a `visual:` criterion that cannot be decided from its named artifact alone, a `mode: generate` ticket with no `- input:` bullet and no prompt in `## Goal / Why`, and a ticket whose text or Context shows the `review_visual` route resolving to the same provider and model as the generator's `implement` route; (2) the correctness reviewer judges a graphics ticket's code and the provenance of the committed artifact (a select commit matching a graded candidate), never the picture, which `review_visual` judges. Why: without these rules an undecidable visual criterion or a self-judging route passes requisition, and the correctness reviewer either grades pictures it cannot see or ignores that a committed artifact was not selected.

## Boundary contract
### Requisition review graphics rules
- disposition: extend
- owner: clutch/specs/requisition_review.md
- consumers: the requisition stage and the Author stage, which acts on its snag findings
- observable change: three more snag cases for graphics tickets, reported with the existing finding shape
- compatibility: verdict set, reply schema, input names and section list are unchanged; a ticket that is not `kind: graphics` is judged as before
- acceptance: the spec lints clean, keeps its five sections, stays within SPEC_MAX_LINES and carries the next minor version
- tests: new `tests/integration/test_graphics_review_spec_blocks.py` plus the version pins in the fenced existing tests
- post-merge source of truth: clutch/specs/requisition_review.md

### Review provenance rule
- disposition: extend
- owner: clutch/specs/review.md
- consumers: the Review stage and rework findings fed from it
- observable change: a graphics ticket's reviewer checks committed-artifact provenance and ignores the picture, using the existing `acceptance` code
- compatibility: verdict set, finding codes (`logic`, `acceptance`, `scope`, `leak`, `ticket`), inputs and section list are unchanged
- acceptance: the spec lints clean, keeps its five sections, stays within SPEC_MAX_LINES and carries the next minor version
- tests: new `tests/integration/test_graphics_review_spec_blocks.py` plus the version pins in the fenced existing tests
- post-merge source of truth: clutch/specs/review.md

## Scope in / Scope out
Scope in:
- clutch/specs/requisition_review.md: add one bullet to the `## Task` snag list, before the line `Report every finding in this one reply; never stop at the first.`, stating the three graphics snag cases above and that a `visual:` criterion naming a declared artifact with a concrete visible outcome is not a hit. Bump `version` to the next minor above the version on main.
- clutch/specs/review.md: add one paragraph to `## Task`, after the `leak` bullet and before `Admissibility:`, saying that for a `kind: graphics` ticket the reviewer judges the code and the provenance of each committed artifact, never the picture; a declared artifact committed with no `clutch(<stem>): select` commit naming it, or a select commit naming no graded candidate for it, is an `acceptance` snag attached to the changed line. No new finding code. Bump `version` to the next minor above the version on main (after `boundary-contract-implementation-review` merges).
- Neither block adds a `## ` heading (tests/unit/test_specs.py pins the section list to Role, Task, Inputs, Output format, On-failure), and each spec stays within SPEC_MAX_LINES (200; 118 and 122 lines at HEAD).
- tests/unit/test_specs.py: move only the `requisition_review` version in the tuple of `test_spec_lint_accepts_the_implement_and_requisition_specs` and the two `spec.meta.version == "<review version>"` asserts in `test_review_spec_read_only` and `test_review_spec_checks_docs`; no other expectation changes.
- tests/integration/test_specs_delimiter_note.py: move only the `("requisition_review", ...)` and `("review", ...)` version pins.
- tests/integration/test_stages.py: move only the `review.spec_version == "<review version>"` assertion in `test_implement_check_review_all_ok_with_artifacts_and_provenance`; no other change and no new tests in that file (the bump forces this edit).
- tests/integration/test_graphics_review_spec_blocks.py (new): the tests below.

Scope out: the implement, author and review_visual specs (the implement graphics block is already merged), any engine code, authoring guide text, a new finding code, and `docs/` (no document describes these spec rules).

## Scope fence
- clutch/specs/requisition_review.md
- clutch/specs/review.md
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_stages.py
- tests/integration/test_graphics_review_spec_blocks.py

## Acceptance criteria
1. `clutch/specs/requisition_review.md` loads with `load_spec`, `lint_spec` returns `[]`, its body headings equal `SPEC_SECTIONS`, it has at most `SPEC_MAX_LINES` lines, and its Task text names a `visual:` criterion undecidable from its artifact, a `generate` ticket with no input and no prompt, and a `review_visual` route resolving to the generator's model as snag cases; `tests/integration/test_graphics_review_spec_blocks.py` asserts each phrase and fails on the HEAD spec, not merely on a version string.
2. `clutch/specs/review.md` loads and lints clean with the same section and line limits, its Task text says a graphics ticket is judged on code and artifact provenance, names the select commit matching a graded candidate, and states the picture is `review_visual`'s; the same test asserts these phrases and that the code list is still exactly `logic`, `acceptance`, `scope`, `leak` (a new finding code fails it).
3. Both specs carry the next minor version above main's and every pin matches: `./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_stages.py` exits 0, and a stale pin in any of the three would fail it.
4. Both specs still render: the new test renders each with fixture inputs and `validate_data_blocks` returns `[]`.

## Verification
```
./dev.py test tests/integration/test_graphics_review_spec_blocks.py tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_stages.py
```

## Definition of rejected
A new `## ` section, finding code, verdict or input name; a version set to a literal other than the next minor above main's; a pin left stale or any test edited beyond the named pins; any edit outside the fence; a rule telling the correctness reviewer to judge the picture.

## Time budget
- expected: 12m
- stuck: 24m
