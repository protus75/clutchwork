---
state: confirmed
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- boundary-contract-authoring

## Context
- clutch/docs/host-authoring.md#What each section is for

## On-demand
- clutch/specs/implement.md
- clutch/specs/review.md

## Goal / Why
Roadmap row 153, Phase 3 of `docs/boundary-contract-plan.md`. Today Implement may pick an API, parameter, failure mode or owner that the ticket's `## Boundary contract` leaves open, and Review does not compare the diff's changed boundaries and consumers with the declared owners. After this ticket: (1) `clutch/specs/implement.md` tells the implementer to reply `premise_failed`, naming the omitted choice, when a material contract choice (a public signature, output variant, error mode, persistence format, or owner) is not decided by the ticket or an existing canonical owner, and never to decide it during implementation; (2) `clutch/specs/review.md` tells the reviewer to `snag` a diff that adds a boundary the ticket does not declare, or a second owner, parser or registry for something a declared or existing canonical owner already provides, and to check changed consumers against the declared owner. No new finding code is added: these findings use the existing `acceptance` and `scope` codes. Why: incidents of duplicate owners and implementation-time policy are the failure the plan measures; the measurement comparison (premise failures, rework, duplicate-owner findings against the trial baseline) is read from the journal by the owner after merge and is not code in this diff.

## Boundary contract
### Implement outcome contract
- disposition: extend
- owner: clutch/specs/implement.md
- consumers: the Implement stage and its `premise_failed` handling in the runner
- observable change: an omitted material contract choice yields outcome `premise_failed` with a finding naming the choice, instead of an implementer-made decision
- compatibility: the four outcomes (`ok`, `already_satisfied`, `premise_failed`, `incomplete`) and the reply schema are unchanged; tickets without a `## Boundary contract` section are not required to have one
- acceptance: the spec parses, lints clean and carries the next minor version
- tests: spec load and version pin tests
- post-merge source of truth: clutch/specs/implement.md

### Review conformity contract
- disposition: extend
- owner: clutch/specs/review.md
- consumers: the Review stage and rework findings fed from it
- observable change: reviewer snags undeclared boundaries and parallel ownership with existing finding codes
- compatibility: the verdict set and finding code vocabulary (`logic`, `acceptance`, `scope`, `leak`, `ticket`) are unchanged
- acceptance: the spec parses, lints clean and carries the next minor version
- tests: spec load and version pin tests
- post-merge source of truth: clutch/specs/review.md

## Scope in / Scope out
Scope in: add the premise rule to `clutch/specs/implement.md` beside the existing `premise_failed` definition; add the diff-conformity rule to the Task list of `clutch/specs/review.md` as `acceptance`/`scope` snag cases attached to a changed line; bump each spec `version` to the next minor above the version on main; update the version pins in the fenced tests (`tests/unit/test_specs.py`, `tests/integration/test_implement_spec_mutation_check.py`, `tests/integration/test_specs_delimiter_note.py`) and nothing else in them; in `tests/integration/test_stages.py` update exactly two pins and nothing else: the review `spec_version` assertion (line 332) and the run.md `- spec: implement 2.20` assertion (line 341), each set to its bumped version; add one new test file for the new rules.
Scope out: no new finding code, no reply schema change, no lint or gate code, no measurement tooling, no edit to the plan document, no change to authoring specs.

## Scope fence
- clutch/specs/implement.md
- clutch/specs/review.md
- tests/unit/test_specs.py
- tests/integration/test_implement_spec_mutation_check.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_stages.py
- tests/integration/test_boundary_contract_spec_rules.py

## Acceptance criteria
1. `clutch/specs/implement.md` parses with `load_spec`, its `version` is the next minor above main's, and the version pins in `tests/unit/test_specs.py`, `tests/integration/test_implement_spec_mutation_check.py`, `tests/integration/test_specs_delimiter_note.py` and the run.md `spec: implement` pin in `tests/integration/test_stages.py` match it; `./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_mutation_check.py tests/integration/test_stages.py` exits 0, and a stale pin would fail it.
2. `clutch/specs/review.md` parses with `load_spec`, carries the next minor version, and the `spec_version` assertion in `tests/integration/test_stages.py` matches it; checked by `./dev.py test tests/integration/test_stages.py`.
3. `tests/integration/test_boundary_contract_spec_rules.py` asserts that the Implement spec text names `premise_failed` for an omitted material contract choice, and that the Review spec text names undeclared boundaries and parallel ownership as `snag` cases; the test fails on the unedited main versions of both specs, checked by `./dev.py test tests/integration/test_boundary_contract_spec_rules.py`.
4. The Review spec's finding code list is unchanged: `lint_spec` on `clutch/specs/review.md` reports no finding and the new test asserts no new code string appears in its code list, checked by `./dev.py test tests/integration/test_boundary_contract_spec_rules.py`.
5. The Implement reply schema is unchanged: the four outcome names appear in `clutch/specs/implement.md` and `premise_failed` still requires at least one finding, checked by `./dev.py test tests/integration/test_boundary_contract_spec_rules.py`, which fails if an outcome name is dropped from the Output format of `clutch/specs/implement.md` or the sentence saying `premise_failed` carries at least one finding is removed.

## Verification
```
./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_mutation_check.py tests/integration/test_boundary_contract_spec_rules.py tests/integration/test_stages.py
```

## Definition of rejected
A new finding code or outcome, a version bumped to a literal other than the next minor, a rule that lets Implement decide an omitted contract choice, any edit outside the fence, or a standing test pinning roadmap or plan text.

## Time budget
- expected: 15m
- stuck: 30m
