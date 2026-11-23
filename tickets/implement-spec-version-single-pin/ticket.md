---
state: confirmed
source: box:retro_finding
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- tests/unit/test_specs.py::test_spec_lint_accepts_the_implement_and_requisition_specs
- tests/unit/test_specs.py::test_implement_spec_consumer_read
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_implement_spec_meta_headers.py
- tests/integration/test_implement_spec_mutation_check.py
- tests/integration/test_stages.py::test_implement_check_review_all_ok_with_artifacts_and_provenance

## Goal / Why
After this ticket, the literal Implement spec version (now `2.27`) appears in exactly one test, `test_implement_spec_consumer_read` in `tests/unit/test_specs.py`. A spec bump then forces an edit in that one file, not in six.

Why: retro finding retro/70 (records 000818 and 000920 declined this earlier, when the evidence was only extra authoring rounds). Two tickets, `check-owns-meta-headers` (attempt 0, pins at 2.23) and `implement-skips-full-suites` (attempt 0, 2.24), bumped the Implement spec. Each fence missed hand-copied pins in `tests/integration/test_implement_spec_mutation_check.py` and `tests/integration/test_stages.py`. Each then failed Implement as premise_failed, which spent a premise_bounce cap, a reject diagnosis and a Reject-queue hold. The pins are still there on HEAD, at 2.27.

Overcorrection guard: one literal pin stays, so an accidental version change or a missed bump is still caught. The `test_stages.py` run-record assertion still checks that the `- spec: implement ` line is rendered, with its version taken from the loaded spec.

## Boundary contract
none
- reason: tests encoding an existing contract. Only test files change, and the version in `clutch/specs/implement.md` and every consumer stay as they are.

## Scope in / Scope out
Scope in:
- `tests/unit/test_specs.py`: keep the literal `2.27` in `test_implement_spec_consumer_read` as the single designated pin. In `test_spec_lint_accepts_the_implement_and_requisition_specs`, drop the literal for the `implement` entry. It still lints and checks `llm_surface` and line count, and its version is not asserted. The other specs' versions stay as they are.
- `tests/integration/test_specs_delimiter_note.py`: drop the literal version for the `implement` parametrize entry. Its version assertion is skipped for that entry only, and the delimiter-note assertions still run. The other specs' versions stay.
- `tests/integration/test_implement_spec_meta_headers.py`: delete `test_implement_spec_meta_header_version`. Keep the clause test.
- `tests/integration/test_implement_spec_mutation_check.py`: remove the `== "2.27"` version assertion. Keep its other assertions. Remove `from clutch.specs import load_spec` (line 11), since the version assertion is its only use in the file. If the assertion is the only content of its test function, delete that function.
- `tests/integration/test_stages.py`: in the run-record assertion, build the expected `- spec: implement <version>` line from the version of the loaded implement spec. Add the import the new name needs. The `- provider: fake\n- model: fake\n- spec: implement ` prefix is still asserted literally.
- Check owns every `clutch:meta` header, including the purpose line, for each file this diff changes. Do not add, edit or refresh any `clutch:meta` header line, even where a purpose line still mentions `2.27` (for example, the purpose line on line 4 of `tests/integration/test_implement_spec_mutation_check.py`). Leave those lines as they are.

Scope out: the Implement spec file itself, any other spec's version pins, any `clutch:meta` header line, and the `slip.produced_by_spec_version == 2` assertion. Do not add new tests, helpers or a shared constant.

## Scope fence
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_implement_spec_meta_headers.py
- tests/integration/test_implement_spec_mutation_check.py
- tests/integration/test_stages.py

## Acceptance criteria
1. `grep -rlF '"2.27"' tests` prints exactly `tests/unit/test_specs.py`. It does not print the delimiter-note, meta-headers or mutation-check test files, which the fix removes.
2. `grep -rF 'implement 2.27' tests` prints nothing. `tests/integration/test_stages.py` no longer hardcodes the version in the run-record assertion.
3. `./dev.py test tests/integration/test_stages.py -k all_ok_with_artifacts_and_provenance` passes. The assertion still contains the literal `- spec: implement ` prefix, so a missing `spec:` line fails and not only a mismatched version.
4. `./dev.py test tests/unit/test_specs.py -k consumer_read` passes with the literal `2.27` still asserted. Changing `version:` in `clutch/specs/implement.md` fails this test and no other test file.
5. `./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_meta_headers.py tests/integration/test_implement_spec_mutation_check.py` passes.

## Verification
```
./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_meta_headers.py tests/integration/test_implement_spec_mutation_check.py tests/integration/test_stages.py
```

## Definition of rejected
A branch is rejected if it removes the single literal pin, so a version change no longer fails any test. It is also rejected if the run-record assertion stops checking that the `spec:` line is rendered, if it adds a new constant or helper module, if it hand-edits a `clutch:meta` header line, or if it edits a file outside the fence.

## Time budget
- expected: 15m
- stuck: 30m