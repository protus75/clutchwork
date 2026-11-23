---
state: confirmed
source: box:retro_finding
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
- implement-spec-version-single-pin

## Context
- tests/integration/test_implement_spec_meta_headers.py
- tests/unit/test_specs.py

## On-demand
- clutch/specs/implement.md

## Goal / Why
Step 5 of `clutch/specs/implement.md` tells Implement that a meta finding on a file the diff does not touch goes to `second_problems`. The engine files each second problem to the Suggestion Box, so 14 Implement replies in the retro/66 window filed the same pre-existing repository-wide `clutch meta check` findings on untouched files. These include missing, drifted or empty-purpose headers, and several replies noted the findings were already on the base commit. Tombstones 000894 to 000957 are mostly this repeat filing, and each one costs a triage call. Merged `check-owns-meta-headers` and `implement-spec-meta-headers-from-verbs` moved header writing to Check but kept this routing sentence, so no open or merged ticket covers it.

When this ticket is done, step 5 keeps the rule that Check writes headers for every file the diff adds or changes. It also says pre-existing metadata findings outside the diff stay outside Implement's work and are omitted from `second_problems`. Check's metadata handling covers the files the diff adds or changes. Implement still reports any other kind of second problem, and still reports a meta defect that its own diff introduces.

## Boundary contract
### Implement prompt spec step 5
- disposition: extend
- owner: clutch/specs/implement.md
- consumers: the Implement stage prompt, `second_problems` filing to the Suggestion Box
- observable change: one sentence in step 5 replaces the untouched-file routing to `second_problems` with a never-report, never-fix statement limited to pre-existing findings outside the diff; the spec version moves to the next minor above the version on main
- compatibility: the sentence that Check writes headers for every file the diff adds or changes is kept; every other `second_problems` rule is unchanged
- acceptance: a test on the spec text fails if the old routing sentence returns or the new statement is dropped
- tests: tests/integration/test_implement_spec_meta_headers.py plus the version pins listed in Scope fence
- post-merge source of truth: clutch/specs/implement.md

## Scope in / Scope out
Scope in:
- In `clutch/specs/implement.md` step 5, keep the checked change scope and replace the sentence that sends untouched-file metadata findings to `second_problems`. State that Implement leaves pre-existing metadata findings outside the diff alone and does not report them in `second_problems`. Check's metadata work covers the files the diff adds or changes. Keep the preceding sentences and the general second-problem rule.
- Bump the spec version to the next minor above main. After `implement-spec-version-single-pin` merges, update only the Implement version assertion remaining in `tests/unit/test_specs.py`. Update the clause assertions in `tests/integration/test_implement_spec_meta_headers.py`; it no longer pins a version.

Scope out: Check, repository-wide meta scans, and existing Suggestion Box messages.

## Scope fence
- clutch/specs/implement.md
- tests/integration/test_implement_spec_meta_headers.py
- tests/unit/test_specs.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_implement_spec_meta_headers.py` proves step 5 directs Implement to leave pre-existing metadata findings outside the diff alone and omit them from `second_problems`. The test fails on the old filing instruction or a claim that Check refreshes unrelated files.
2. `./dev.py test tests/integration/test_implement_spec_meta_headers.py` preserves the sentence saying Check writes headers for every file the diff adds or changes.
3. `./dev.py test tests/unit/test_specs.py` checks the sole Implement version pin against the bumped spec.

## Verification
```
./dev.py test tests/integration/test_implement_spec_meta_headers.py tests/unit/test_specs.py
```

## Definition of rejected
The branch changes any Implement spec rule other than step 5 and the version, drops the rule that Check writes headers for files the diff adds or changes, stops Implement from reporting other kinds of second problems, or edits Check or meta code.

## Time budget
- expected: 12m
- stuck: 24m
