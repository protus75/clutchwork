---
state: confirmed
source: human
priority: P0
kind: feature
---

## Depends on
- check-owns-meta-headers

## Context
- tests/unit/test_specs.py::test_implement_spec_consumer_read
- tests/integration/test_implement_spec_meta_headers.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_implement_spec_mutation_check.py

## On-demand
- clutch/specs/implement.md
- docs/how-clutch-works.md

## Goal / Why
Implement attempts spend much of their time running test suites that Check runs anyway. Rule 3 of the Implement prompt tells the model to run every hard always-trigger host Check entry, including the full unit and integration suites, after its last edit. When anything fails it reruns on a base-commit worktree, then an isolated rerun, then one more full run. On 2026-11-21 `roadmap-meta-resync`, a 2-line metadata change, timed out in Implement after 363 s, most of it in full pytest runs. Check then ran the same suites again. After this ticket Implement runs only the ticket's `## Verification` commands and lint and format on the files it changed. Check alone runs the full suites, the coverage gates and the base comparisons, and its failures reach the next attempt through Diagnose as today.

## Boundary contract
### Implement prompt test runs
- disposition: replace
- owner: clutch/specs/implement.md
- consumers: Implement
- observable change: rule 3 tells Implement to run each `## Verification` command as written and lint and format on the files it changed, and never to run the full host Check suites, coverage gates, base-commit worktree comparisons or isolated reruns for failures outside Verification; a `## Verification` failure keeps today's handling (fix it, or report it with a base-commit rerun of that Verification command only)
- compatibility: rules 1, 2 and 4 onward are unchanged; Check's gates are unchanged; `version` bumps to the next minor above main
- acceptance: criteria 1 and 2
- tests: tests/unit/test_specs.py and tests/integration/test_implement_spec_runs.py
- post-merge source of truth: clutch/specs/implement.md

## Scope in / Scope out
Scope in:
- clutch/specs/implement.md rule 3: delete the sentences that make Implement run the hard always-trigger host Check entries and the coverage gates, and the intermittent-failure paragraph built on them ("When a failing test passes on the base commit and fixing it would require an edit outside..." through "...stays a `premise_failed` finding."). Replace them with one sentence: run lint and format only on the files the diff changes, and leave the full suites, coverage gates and base comparisons to Check, whose failures come back as retry findings. Keep the base-commit rerun only for a failing `## Verification` command. Bump `version` to the next minor above main (2.24 to 2.25).
- tests/unit/test_specs.py: in `test_implement_spec_consumer_read`, drop the assertions that pin the deleted sentences, and update the `implement` version pins (line 33 in `test_spec_lint_accepts_the_implement_and_requisition_specs`, and line 134). Nothing else changes there.
- tests/integration/test_specs_delimiter_note.py, tests/integration/test_implement_spec_meta_headers.py and tests/integration/test_implement_spec_mutation_check.py: update the `implement` version pin only.
- tests/integration/test_stages.py: update the `spec: implement 2.24` provenance pin at line 350 only. This is a hot test file; the version bump forces this one-line edit and nothing else is added there.
- docs/how-clutch-works.md: replace the two sentences saying Implement runs the host hard always-trigger checks and hard coverage gates after its last edit with one sentence saying Implement runs its Verification commands and lint and format on changed files, and leaves the full suites, coverage gates and base comparisons to Check.
- New tests/integration/test_implement_spec_runs.py reads the shipped spec through a `Path(__file__)` anchor.
Scope out:
- Check, gates, host Check entries in config.yaml, the Diagnose prompt, and Implement's other rules.

## Scope fence
- clutch/specs/implement.md
- docs/how-clutch-works.md
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_implement_spec_meta_headers.py
- tests/integration/test_implement_spec_mutation_check.py
- tests/integration/test_stages.py
- tests/integration/test_implement_spec_runs.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_implement_spec_runs.py` proves the rendered Implement Task no longer contains "Run each hard always-trigger host Check entry", "hard coverage gate" or "one further full run", and does contain the new sentence leaving the full suites, coverage gates and base comparisons to Check.
2. `./dev.py test tests/integration/test_implement_spec_runs.py` proves the Task still tells Implement to run every `## Verification` command and to rerun a failing `## Verification` command on a base-commit worktree before calling it base-red.
3. `./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_meta_headers.py tests/integration/test_implement_spec_mutation_check.py tests/integration/test_stages.py` passes with the bumped version.

## Verification
```
./dev.py test tests/integration/test_implement_spec_runs.py tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_meta_headers.py tests/integration/test_implement_spec_mutation_check.py tests/integration/test_stages.py
```

## Definition of rejected
Implement still told to run a full suite, Check gates changed, or files outside the fence change.

## Time budget
- expected: 8m
- stuck: 16m