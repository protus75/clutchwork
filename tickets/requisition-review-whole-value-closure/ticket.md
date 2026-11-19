---
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
source: box:retro_finding
state: confirmed
---

## Depends on
- none

## Context
- tests/integration/test_fence_closure_registries.py
- tests/integration/test_specs_delimiter_note.py
- tests/unit/test_specs.py

## On-demand
- clutch/specs/requisition_review.md

## Goal / Why
Requisition review approved `unit-coverage-drop-test-contexts` twice (spec 3.22) while `tests/integration/test_fixture_host.py`, outside the fence, asserted `cfg.review.mechanical[0].model_dump() == {...}` exactly. Scope in added the field `MechanicalCheck.flake_coverage_argv`, so that equality had to fail. The reviewer marked the file `unaffected` with the reason "reads config.yaml as a loadable config", which cites no asserting line. Implement then returned premise_failed, which cost a run, a premise_bounce cap unit, a diagnosis and a rework. The same class broke the GOLDEN render in `tests/integration/test_hostfiles.py` after a CORE_TEMPLATE edit.

The fence-closure rules in `clutch/specs/requisition_review.md` trace symbol references, recorded values of bumped constants, and set or collection members. None covers a field change to a model, dataclass or config type, or a change to rendered text, that a test compares as a whole. The dependents rule also lets an `unaffected` reason cite only "the input read". After this ticket the spec carries a whole-value closure bullet and requires an `unaffected` reason for a dependent that reads a changed type or render to cite the asserting line it checked. The closure is limited to whole-value equality; a test that only builds or loads the model, or asserts fields the change leaves alone, is not a hit.

This is not the set-membership closure (`set-membership-fence-closure`), which covers set and collection members, not model fields or render bytes.

## Boundary contract
### Requisition review prompt spec
- disposition: extend
- owner: clutch/specs/requisition_review.md
- consumers: the requisition review stage that renders this spec, and the version pins in tests/unit/test_specs.py and tests/integration/test_specs_delimiter_note.py
- observable change: the reviewer is told to grep `tests/` for whole-value comparisons of a changed type's serialized form or a changed render, and to cite the asserting line in any `unaffected` reason for a dependent reading that type or render
- compatibility: the existing symbol-closure, recorded-value-closure and set-membership text is unchanged; the reply schema is unchanged
- acceptance: the new bullet and the dependents-rule sentence are present in the spec body and both version pins match the bumped version
- tests: a new integration test reads the spec and asserts the phrases; the pins in tests/unit/test_specs.py and tests/integration/test_specs_delimiter_note.py move
- post-merge source of truth: clutch/specs/requisition_review.md

## Scope in / Scope out
- In: `clutch/specs/requisition_review.md`: add one fence-closure bullet after the set-membership bullet. It says that when Scope in adds, removes or renames a field of a model, dataclass or config type, or changes text a render function emits, the reviewer greps `tests/` for whole-value comparisons of that type's serialized form or that render (`model_dump()`, `asdict`, `dict(...) ==`, golden bytes, base64 or digest constants) and fences every hit or raises a snag. It states the limit: only whole-value equality is a hit, and a test that only builds or loads the model, or asserts fields the change leaves alone, is not.
- In: the same file, dependents rule: add that an `unaffected` reason for a dependent that reads a changed type or render must cite the asserting `file:line` it checked, not only the input file the test loads.
- In: bump the spec `version` to the next minor above its value on main at authoring time (3.22 when drafted; sibling tickets may have bumped it since).
- In: `tests/unit/test_specs.py`: only the `requisition_review` version pin on the tuple of spec versions moves to the bumped version.
- In: `tests/integration/test_specs_delimiter_note.py`: only its `("requisition_review", "3.22")` version pin moves to the bumped version.
- In: new `tests/integration/test_requisition_review_whole_value_closure.py` reading the spec through a `Path(__file__)` anchor and asserting the new phrases.
- Out: every other spec, engine code, docs, any lint, and the set-membership bullet text.

## Scope fence
- clutch/specs/requisition_review.md
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_requisition_review_whole_value_closure.py

## Acceptance criteria
1. The spec body contains the phrases `changes text a render function emits` and `whole-value comparisons`. `./dev.py test tests/integration/test_requisition_review_whole_value_closure.py` asserts both, which rules out the base spec that has no such closure.
2. The spec body contains the limit phrase `only whole-value equality is a hit`. The same test asserts it, which rules out a rule that fences every test that merely loads the model.
3. The dependents rule contains `must cite the asserting` and `file:line`. The same test asserts it on the dependents line, which rules out an `unaffected` reason that cites only the input file.
4. The spec `version` is one minor above its value at the base commit, and `./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py` passes with both pins moved, which rules out an unbumped version or a stale pin in either file.
5. The existing closure text still holds: `./dev.py test tests/integration/test_fence_closure_registries.py` passes unchanged, which rules out weakening the set-membership or symbol closure.

## Verification
```
./dev.py test tests/integration/test_requisition_review_whole_value_closure.py
./dev.py test tests/unit/test_specs.py
./dev.py test tests/integration/test_specs_delimiter_note.py
./dev.py test tests/integration/test_fence_closure_registries.py
./dev.py test tests/integration/test_precondition_rules.py
```

## Definition of rejected
The limit to whole-value equality is missing; the dependents rule does not require a cited asserting line; the version is not bumped or either pin keeps the old value; existing closure text is weakened; any file outside `## Scope fence` changes.

## Time budget
- expected: 15m
- stuck: 30m
