---
state: draft
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
source: box:retro_finding
---

## Depends on
none

## Context
- tests/unit/test_specs.py::test_requisition_review_spec_raises_impossible_criteria_unchanged
- tests/integration/test_specs_delimiter_note.py

## On-demand
- clutch/specs/requisition_review.md

## Goal / Why
Retro finding retro/60: requisition review approved `meta-schema-and-refresh-r2` twice although its Scope in had refresh insert an 8-9 line meta block into every file under `meta.paths` (about 600 files). Attempt 1 then failed the `diff_budget` check with 5512 inserted lines against a 1500 budget, and Diagnose had to split the ticket. `clutch/specs/requisition_review.md` has no rule comparing the edit volume Scope in requires with the diff budget, so a ticket that cannot pass the gate as written is approved and the cost appears only after a full Implement and Check cycle. The merged `meta-annotate-*` stems repaired that instance; this ticket adds the review rule that catches the class. It does not re-solve `declined-box-000825` (uv.lock counting) or `declined-box-000443` (codex on wide tickets).

After this ticket the review spec tells the reviewer: when Scope in requires one fixed mechanical edit repeated across a countable path set, estimate inserted lines as files times lines per file, and if that product exceeds the repo's diff budget, raise a `snag` whose paved road splits the work into a code stem plus path-sharded stems, each under budget and each depending on the code stem. The rule never applies to estimates of hand-written code size.

## Boundary contract
### Requisition review spec
- disposition: extend
- owner: clutch/specs/requisition_review.md
- consumers: the requisition review stage that renders this spec for every authored ticket
- observable change: a ticket whose Scope in requires a fixed per-file edit across N files, with N times lines-per-file over the diff budget, gets a `snag` with a split road; other tickets are unaffected
- compatibility: reply schema, existing rules and other specs are unchanged; the `version` is bumped to the next minor above the version on main
- acceptance: the rendered Task text contains the countable-volume rule, the product-over-budget condition, the split paved road, and the guard against hand-written code estimates
- tests: phrase test in a new unit test file plus updated version pins
- post-merge source of truth: clutch/specs/requisition_review.md

## Scope in / Scope out
Scope in: add one bullet to the Task section of `clutch/specs/requisition_review.md` stating the rule above. Apply it only when the required volume is countable from Scope in (file count times a fixed per-file edit, such as one block per file, a rename across a tree, or a regenerated artifact) and the product clearly exceeds the diff budget; never to guesses of hand-written code size. The paved road names a code stem plus path-sharded stems, each under budget and each listing the code stem in `## Depends on`. Keep the spec within `SPEC_MAX_LINES`. Bump the spec `version` to the next minor above the version on main, and update the version pin in `tests/unit/test_specs.py` (`test_spec_lint_accepts_the_implement_and_requisition_specs`) and in `tests/integration/test_specs_delimiter_note.py`. Add the phrase test in a new file `tests/unit/test_specs_requisition_diff_budget.py`, modeled on the existing phrase tests in `tests/unit/test_specs.py`.
Scope out: any engine code, gate, or config change; counting `uv.lock`; Diagnose, Implement, Review and Rework specs; other requisition rules.

## Scope fence
- clutch/specs/requisition_review.md
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py
- tests/unit/test_specs_requisition_diff_budget.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_specs_requisition_diff_budget.py` passes; it asserts the rendered Task contains the phrases for files times lines per file, exceeding the diff budget, the split into a code stem and path-sharded stems each depending on the code stem, and the guard that hand-written code size is never estimated. A spec lacking any phrase fails it.
2. `./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py` passes with the bumped requisition_review version pins; the old version string no longer passes.
3. `./dev.py test tests/unit/test_specs.py` confirms `lint_spec` returns `[]` and the spec has at most `SPEC_MAX_LINES` lines.

## Verification
```
./dev.py test tests/unit/test_specs_requisition_diff_budget.py tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py
```

## Definition of rejected
The branch changes anything outside the fence, adds a rule that snags ordinary multi-file tickets or estimates hand-written code size, hardcodes a diff budget number in the spec, or states the version bump as a literal target different from the next minor.

## Time budget
- expected: 10m
- stuck: 20m
