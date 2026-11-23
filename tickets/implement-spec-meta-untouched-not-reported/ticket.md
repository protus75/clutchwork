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

When this ticket is done, step 5 keeps the rule that Check writes headers for every file the diff adds or changes. It also says findings on files the diff does not add or change belong to Check's meta refresh and the `meta_drift` gate, are never reported in `second_problems`, and are never fixed in the diff. Implement still reports any other kind of second problem, and still reports a meta defect that its own diff introduces.

## Boundary contract
### Implement prompt spec step 5
- disposition: extend
- owner: clutch/specs/implement.md
- consumers: the Implement stage prompt, `second_problems` filing to the Suggestion Box
- observable change: one sentence in step 5 replaces the untouched-file routing to `second_problems` with a never-report, never-fix statement naming Check's meta refresh and the `meta_drift` gate as owners; the spec version moves to the next minor above the version on main
- compatibility: the sentence that Check writes headers for every file the diff adds or changes is kept; every other `second_problems` rule is unchanged
- acceptance: a test on the spec text fails if the old routing sentence returns or the new statement is dropped
- tests: tests/integration/test_implement_spec_meta_headers.py plus the version pins listed in Scope fence
- post-merge source of truth: clutch/specs/implement.md

## Scope in / Scope out
Scope in:
- In `clutch/specs/implement.md` step 5, replace only the sentence "A meta finding on a file the diff does not touch goes to `second_problems`; never fix it in this diff." with a statement that meta findings on files the diff does not add or change are owned by Check's meta refresh and the `meta_drift` gate, are never reported in `second_problems`, and are never fixed in this diff. Keep the preceding sentences unchanged.
- Bump the spec `version` to the next minor above the version on main.
- Update the sentence list in `tests/integration/test_implement_spec_meta_headers.py` to the new sentence, and update the version pins in the fenced tests below. Each pin changes only its version value.

Scope out: any other Implement spec rule, Check or meta code, the `meta_drift` gate, and `docs/` text. Repeat-filing cleanup of existing Suggestion Box messages is not done here.

## Scope fence
- clutch/specs/implement.md
- tests/integration/test_implement_spec_meta_headers.py
- tests/integration/test_implement_spec_mutation_check.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_stages.py
- tests/unit/test_specs.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_implement_spec_meta_headers.py` passes; it asserts the new step 5 sentence is present and that the old text "A meta finding on a file the diff does not touch goes to `second_problems`" is absent, so a spec still routing untouched-file findings to `second_problems` fails.
2. `./dev.py test tests/integration/test_implement_spec_meta_headers.py` also asserts the sentence "Check writes headers for every file the diff adds or changes." is present, so dropping the rule for diff-changed files fails.
3. `./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_mutation_check.py` passes with every Implement version pin at the new version, and no pin still reads the old version.
4. `./dev.py test tests/integration/test_stages.py` passes with its run-record assertion naming the new `implement` spec version, not the old one.

## Verification
```
./dev.py test tests/integration/test_implement_spec_meta_headers.py tests/integration/test_implement_spec_mutation_check.py tests/integration/test_specs_delimiter_note.py tests/integration/test_stages.py tests/unit/test_specs.py
```

## Definition of rejected
The branch changes any Implement spec rule other than step 5 and the version, drops the rule that Check writes headers for files the diff adds or changes, stops Implement from reporting other kinds of second problems, or edits Check or meta code.

## Time budget
- expected: 12m
- stuck: 24m
