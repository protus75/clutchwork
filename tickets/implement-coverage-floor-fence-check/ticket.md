---
state: confirmed
source: box:retro_finding
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
- implement-spec-version-single-pin

## Context
- tests/integration/test_implement_spec_runs.py
- tests/unit/test_specs.py::test_implement_spec_consumer_read
- test-gate.toml

## On-demand
- clutch/specs/implement.md

## Goal / Why
Retro finding retro/33 reopens a request that earlier registry records 000367, 000373 and 000379 tombstoned and that merged ticket `implement-skips-full-suites` reversed on purpose: Implement must not run the full suites or coverage gates, because Check runs them and Diagnose carries failures back. This ticket keeps that decision. It closes only the cheap part of the finding. Attempts of `results-schema-2-reader` (attempt 0), `review-lock-only-for-intake` (attempt 0) and `core-drift-preflight` (attempt 2) reported `ok` after only the Verification command. The unit coverage gate then failed at Check because no fenced unit test ran the added lines. In one of them the diagnosis told the agent to reshape production code so it gains no statements.

After this ticket, rule 3 of the Implement prompt has Implement do a read-only check before it reports `ok`. When the diff adds lines to a file with a positive `[coverage.files]` floor in `test-gate.toml`, a fenced `tests/unit/` test must run those lines. If the fence holds no such path, the agent replies `premise_failed` naming the missing fence path, and never reshapes production code to dodge the floor. The check runs no gate and no full suite. It reads the floor and the fence, and it runs only the unit test files the diff adds or changes.

The retro's reopen condition asks for measured data on Check cost. This ticket does not move the gate into Implement, so that condition does not apply to it.

## Boundary contract
### Implement prompt coverage-floor check
- disposition: extend
- owner: clutch/specs/implement.md
- consumers: Implement
- observable change: rule 3 gains one sentence. Before reporting `ok`, Implement reads `test-gate.toml`. When the diff adds lines to a file with a positive coverage floor, it makes sure a fenced `tests/unit/` test runs them, and it runs only the unit test files it added or changed. When the fence has no `tests/unit/` path for that file, it replies `premise_failed` naming that path and does not change production code to avoid the floor.
- compatibility: the rule 3 sentence leaving full suites, coverage gates and base comparisons to Check stays verbatim. Rules 1, 2 and 4 onward are unchanged, and Check's gates are unchanged. `version` bumps to the next minor above the version on main.
- acceptance: criteria 1 to 3
- tests: tests/integration/test_implement_spec_runs.py, plus the version pins in the existing spec tests
- post-merge source of truth: clutch/specs/implement.md

## Scope in / Scope out
Scope in:
- clutch/specs/implement.md rule 3: add the one sentence described above directly after the sentence that leaves full suites, coverage gates and base comparisons to Check. Bump `version` to the next minor above the version on main.
- tests/integration/test_implement_spec_runs.py: add the new required sentence to the `required` list of `test_implement_task_preserves_verification_and_handoff`, and add one test that the Task still contains the unchanged sentence leaving full suites and coverage gates to Check. This file already tests the shipped Implement spec and is the subject of this change.
- Version pins for the bumped spec, one line each: tests/integration/test_implement_spec_meta_headers.py, tests/integration/test_implement_spec_mutation_check.py, tests/integration/test_specs_delimiter_note.py, tests/integration/test_stages.py (the `spec: implement` provenance pin only) and tests/unit/test_specs.py (the two `implement` version pins only).
Scope out:
- Check, gates and `test-gate.toml`.
- The Diagnose prompt.
- Running coverage gates or full suites inside Implement.
- Rules of the Implement prompt other than rule 3.

## Scope fence
- clutch/specs/implement.md
- tests/integration/test_implement_spec_runs.py
- tests/integration/test_implement_spec_meta_headers.py
- tests/integration/test_implement_spec_mutation_check.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_stages.py
- tests/unit/test_specs.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_implement_spec_runs.py` proves the rendered Implement Task contains the new sentence naming `test-gate.toml`, a positive coverage floor and a fenced `tests/unit/` test. A prompt without the sentence fails the test.
2. `./dev.py test tests/integration/test_implement_spec_runs.py` proves the Task still contains "leave the full suites, coverage gates and base comparisons to Check". A prompt that tells Implement to run the coverage gate itself fails the test.
3. `./dev.py test tests/integration/test_implement_spec_runs.py` proves the Task tells Implement to reply `premise_failed` when the fence has no unit test path, and that the sentence names changing production code to avoid the floor as forbidden.
4. `./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_meta_headers.py tests/integration/test_implement_spec_mutation_check.py tests/integration/test_stages.py` passes with the bumped version pins. A stale pin of 2.27 fails.

## Verification
```
./dev.py test tests/integration/test_implement_spec_runs.py tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_meta_headers.py tests/integration/test_implement_spec_mutation_check.py tests/integration/test_stages.py
```

## Definition of rejected
The Implement prompt tells Implement to run a coverage gate or a full suite, the sentence leaving those to Check is removed, or files outside the fence change.

## Time budget
- expected: 8m
- stuck: 16m
