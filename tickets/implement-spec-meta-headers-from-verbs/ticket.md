---
state: draft
source: box:retro_finding
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/meta.py::parse
- tests/integration/test_implement_spec_mutation_check.py

## On-demand
- clutch/specs/implement.md

## Goal / Why
The Implement prompt says nothing about `clutch:meta` headers. Implementers hand-type them or skip them. `clutch/meta.py::parse` requires all seven keys, including the engine-computed `verified` and `hash`, so a hand-typed header raises Malformed. On `spools-test-helper` attempt 0, all Verification passed, but Review snagged both new files because their headers lacked `verified` and `hash`. That cost a review, a diagnosis and a retry. On `index-build-r2`, attempts 0 and 3 lost a Check to header content. After this ticket the Implement prompt tells the implementer to get a header for a new file under a configured `meta.paths` root only from `clutch meta fill <path>` or `clutch meta refresh`, never to type one, and to put none on a file outside `meta.paths`. It also tells the implementer to run `clutch meta check` after the last edit and fix findings only on files in the diff. Findings on files the diff does not touch go to `second_problems`, so implementers do not spend calls on meta debt already on the base.

## Boundary contract
### Implement prompt spec
- disposition: extend
- owner: clutch/specs/implement.md
- consumers: the Implement stage prompt render, and every host's implementer sessions
- observable change: one new numbered step in `## Task` covering meta headers; the spec `version` moves to the next minor above the version on main; the output format and outcomes are unchanged
- compatibility: all existing steps keep their text; the commit step is renumbered
- acceptance: a test reads the spec text and checks the new step's required clauses and the bumped version
- tests: tests/integration/test_implement_spec_meta_headers.py, plus the four existing pins of the old version
- post-merge source of truth: clutch/specs/implement.md

## Scope in / Scope out
Scope in:
- In `clutch/specs/implement.md`, add a step between the docs-sync step (step 4) and the commit step, and renumber the commit step to follow it. The step says:
  - A new file the diff adds under a configured `meta.paths` root gets its `clutch:meta` header only from `clutch meta fill <path>` or `clutch meta refresh`. Never type or copy a header, because `verified` and `hash` are engine-computed and a hand-typed header fails `parse`.
  - A file outside `meta.paths` gets no header.
  - After the last edit and before replying `ok`, run `clutch meta check` and confirm none of the files the diff adds or changes is reported `malformed`, `missing` or `drifted`.
  - A meta finding on a file the diff does not touch is reported in `second_problems`, never fixed in this diff.
- Bump the spec `version` to the next minor above the version on main. Do not state a literal target.
- Update the version pin in the four existing tests that pin the old version. Each edit changes only the expected version string: tests/integration/test_implement_spec_mutation_check.py, tests/integration/test_specs_delimiter_note.py, tests/unit/test_specs.py, and the `spec: implement` run.md assertion in tests/integration/test_stages.py.
- Add the new test file tests/integration/test_implement_spec_meta_headers.py.

Scope out: `clutch/meta.py`, the meta verbs and any config. Diagnose behavior for engine-written failures is covered by `diagnose-spec-engine-written-failure-abandons`. No other prompt spec changes.

## Scope fence
- clutch/specs/implement.md
- tests/integration/test_implement_spec_meta_headers.py
- tests/integration/test_implement_spec_mutation_check.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_stages.py
- tests/unit/test_specs.py

## Acceptance criteria
1. The new test asserts the spec text contains the clauses that new-file headers come only from `clutch meta fill <path>` or `clutch meta refresh`, that a file outside `meta.paths` gets no header, that `clutch meta check` runs before replying `ok`, and that findings on files the diff does not touch go to `second_problems`. It fails on the base spec, which has none of them. Run `./dev.py test tests/integration/test_implement_spec_meta_headers.py`.
2. `load_spec(text).meta.version` in the new test equals the version on main with its minor part incremented by one, not `2.21`. The four existing pins agree with it. Run `./dev.py test tests/integration/test_implement_spec_mutation_check.py tests/integration/test_specs_delimiter_note.py tests/unit/test_specs.py`.
3. The `spec: implement` run.md assertion in tests/integration/test_stages.py matches the new version, not `2.21`. Run `./dev.py test tests/integration/test_stages.py`.
4. The Implement spec still loads and its existing mutation-check and boundary-contract clauses are unchanged. Run `./dev.py test tests/integration/test_boundary_contract_spec_rules.py`.

## Verification
```
./dev.py test tests/integration/test_implement_spec_meta_headers.py tests/integration/test_implement_spec_mutation_check.py tests/integration/test_specs_delimiter_note.py tests/integration/test_boundary_contract_spec_rules.py tests/unit/test_specs.py tests/integration/test_stages.py
```

## Definition of rejected
The step tells implementers to add headers to files outside `meta.paths`, or to fix meta findings on files the diff does not touch. Any file outside the fence changes. The version is left unbumped or is a literal target written by hand.

## Time budget
- expected: 15m
- stuck: 30m
