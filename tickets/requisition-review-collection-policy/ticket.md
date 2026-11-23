---
state: rejected
source: box:retro_finding
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- tests/integration/test_deferral_rules.py
- tests/unit/test_specs.py::test_requisition_review_spec_snags_missing_reproduction_exit

## On-demand
- clutch/specs/requisition_review.md

## Goal / Why
Requisition review checks that each named test file exists, but not whether the repo's integration collection policy lets the test run. Two tickets were approved and then bounced at Implement as premise_failed. They cost an Implement run, a premise_bounce cap, a reject diagnosis and a rework each (retro/72). `serve-flaky-tests-deterministic` named tests in files that `DISK_IO_SKIP` in `tests/integration/conftest.py` skips (8 passed, 49 skipped, so criteria passed only as skips). `serve-contains-dispatch-exception` required a new test built on `tests/integration/serve_rig.py`, whose real repo `IntegrationIOBlocked` in `clutch/ioguard.py` blocks outside `REAL_IO_TESTS`. When this ticket is done, the review spec tells the reviewer to raise a snag in both cases, so the ticket is repaired before Implement. `requisition-review-unit-disk-read` covers only unit-test disk I/O, and `requisition-review-impossible-criteria-unchanged` does not mention skip or guard policy, so neither covers this.

The rule must send the reviewer to read the policy on HEAD at review time and never hardcode today's skip list, which `disk-io-skip-per-file` and the `restore-io-tests-*` work are shrinking. It applies only when a criterion's or Verification command's proof depends on that test running. A skipped file named only for context or for "unchanged" preservation is not a hit.

## Boundary contract
### Requisition review spec
- disposition: extend
- owner: clutch/specs/requisition_review.md
- consumers: the requisition review stage, which renders the spec as its prompt
- observable change: the Task text adds a snag for criteria whose proof depends on a skipped integration test or on a new integration test that needs a real-I/O helper the guard blocks. It names the paved road: a `## Depends on` edge to the ticket that unskips or converts the file, or an in-fence in-memory fixture (`tests/fakes.py`) with criteria that name tests that run.
- compatibility: existing rules stay as they are; the `version` is bumped to the next minor above the version on main, and the two tests that pin it follow
- acceptance: a phrase test fails when the rule or its limits are dropped
- tests: new `tests/integration/test_requisition_review_collection_policy.py`, plus the two version-pin edits
- post-merge source of truth: clutch/specs/requisition_review.md

## Scope in / Scope out
Scope in:
- Add one rule to the Task section of `clutch/specs/requisition_review.md`. For each test a criterion or Verification command depends on, and each new integration test a criterion requires, the reviewer reads the integration collection policy on HEAD (the skip list in `tests/integration/conftest.py` and the `REAL_IO_TESTS` allowance in `clutch/ioguard.py`). It is a snag when the named test file is skipped so the criterion can pass vacuously, or when a required new test needs a real-I/O helper from a file the guard blocks. The rule names the paved road above. It states that the reviewer reads the policy at review time and does not rely on a remembered list. It states that a skipped file named only for context or unchanged preservation is not a snag.
- Bump the spec `version` to the next minor above the version on main, and update the version literal in the two existing pins: the `requisition_review` entry in `tests/unit/test_specs.py` and the one in `tests/integration/test_specs_delimiter_note.py`. Those are the only expectations that change in those two files.
- Add a new phrase test file for the rule.

Scope out: the skip list and guard code, and all other review rules.

## Scope fence
- clutch/specs/requisition_review.md
- tests/integration/test_requisition_review_collection_policy.py
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py

## Acceptance criteria
1. The rendered Task text of the requisition review spec names `tests/integration/conftest.py`, `REAL_IO_TESTS` and `clutch/ioguard.py`; `./dev.py test tests/integration/test_requisition_review_collection_policy.py` fails when any of the three is removed from the spec text.
2. The rule text states that the policy is read on HEAD at review time, and that a file named only for context or unchanged preservation is not a snag. `./dev.py test tests/integration/test_requisition_review_collection_policy.py` fails when either clause is removed, so a rule that snags every mention of a skipped file does not pass.
3. The rule text names both paved roads, the `## Depends on` edge and the in-fence in-memory fixture `tests/fakes.py`; the same test fails when either is missing.
4. The test asserts the spec does not list a concrete skipped filename such as `test_host_loop.py`, `test_serve_admission.py` or `test_gates.py`, so the rule cannot hardcode today's list (`assert not in`, not a vacuous pass).
5. The `requisition_review` version pins in `tests/unit/test_specs.py` and `tests/integration/test_specs_delimiter_note.py` match the bumped spec, and `./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py` exits 0.

## Verification
```
./dev.py test tests/integration/test_requisition_review_collection_policy.py tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_deferral_rules.py tests/integration/test_precondition_rules.py
```

## Definition of rejected
The rule hardcodes the current skip list, or snags a ticket merely for naming a skipped file as context, or the branch changes the skip list, the guard code, or `clutch/specs/author.md`.

## Time budget
- expected: 15m
- stuck: 30m
