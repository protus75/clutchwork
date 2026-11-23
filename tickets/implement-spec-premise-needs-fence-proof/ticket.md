---
state: draft
source: box:retro_finding
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- tests/integration/test_implement_spec_meta_headers.py
- tickets/implement-spec-base-red-not-premise/ticket.md

## On-demand
- clutch/specs/implement.md

## Goal / Why
Retro finding retro/68. Step 3 of `clutch/specs/implement.md` says a failure that passes on the base commit and requires an edit outside `## Scope fence` remains a `premise_failed` finding. Nothing asks the agent to prove that requirement, so an out-of-fence test that fails only on the candidate is read as proof that the fix is out of fence. On `serve-merge-off-exclusive` attempt 3, `tests/integration/test_host_loop.py` failed twice on the candidate and passed on base. Implement committed nothing and replied `premise_failed`. Diagnose said the call was wrong and that the diff had caused a regression with an in-fence cause (lock order in `merging()` and `dirty_overlap`). That cost an Implement run and an escalation rung, and attempt 4 merged inside the same fence.

After this ticket, Step 3 requires: when an out-of-fence test fails only on the candidate and the failure reproduces, first trace it to the diff's in-fence code path (logs, journal, lock order) and fix it there. `premise_failed` is allowed for it only when a finding names the out-of-fence line that must change and states why no in-fence change can satisfy both that test and the acceptance criteria. A real fence gap (for example a test pinning old behavior) stays `premise_failed` whenever its finding names that line, so the agent must not chase it. Not re-solved here: `implement-premise-names-path` and `implement-all-premise-findings` (naming and listing forced files), `implement-spec-base-red-not-premise` (failures that also fail on base), `implement-spec-intermittent-*` (nondeterminism), `review-spec-out-of-fence-breakage` (Review side), and open `implement-fence-gap-keeps-branch` (keeping the branch after a real gap).

## Boundary contract
### Implement prompt spec
- disposition: extend
- owner: clutch/specs/implement.md
- consumers: the Implement stage prompt and the spec-version pins in tests
- observable change: Step 3 adds the trace-first rule and the two-part proof (named out-of-fence line, reason no in-fence change works) required for a `premise_failed` on a candidate-only out-of-fence failure; the spec version moves to the next minor above main
- compatibility: the reply schema, outcomes and every other step are unchanged; a real fence gap with a named line still replies `premise_failed`
- acceptance: an integration test reads the spec and asserts the new rule text and the version
- tests: tests/integration/test_implement_spec_premise_proof.py
- post-merge source of truth: clutch/specs/implement.md

## Scope in / Scope out
Scope in: edit step 3 of `clutch/specs/implement.md` (the sentence ending at the `premise_failed` finding) to add the rule above in at most four added lines; bump the spec `version` to the next minor above the version on main; update every existing pin of the old version in the fenced tests (`tests/unit/test_specs.py`, `tests/integration/test_specs_delimiter_note.py`, `tests/integration/test_stages.py` line asserting `spec: implement`, `tests/integration/test_implement_spec_meta_headers.py`, `tests/integration/test_implement_spec_mutation_check.py`), changing only the version value in each; add one new integration test file.
Scope out: other steps of the spec, the Review/Diagnose specs, engine code, and keeping the branch after a fence gap (`implement-fence-gap-keeps-branch`). Rule placement: this is an engine prompt rule that lives only in the shipped spec.

## Scope fence
- clutch/specs/implement.md
- tests/integration/test_implement_spec_premise_proof.py
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_stages.py
- tests/integration/test_implement_spec_meta_headers.py
- tests/integration/test_implement_spec_mutation_check.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_implement_spec_premise_proof.py` passes; it asserts that the Step 3 text of the spec tells the agent to trace a candidate-only out-of-fence failure to the diff's in-fence code first, and that `premise_failed` for it requires naming the out-of-fence line and the reason no in-fence change works. A spec lacking either part fails the test.
2. The same test asserts the spec still says a failure that passes on base and requires an edit outside `## Scope fence` is a `premise_failed` finding, so a real fence gap is not forbidden.
3. `./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_meta_headers.py tests/integration/test_implement_spec_mutation_check.py` passes with every pin at the bumped version, not the old `2.27`.
4. `./dev.py test tests/integration/test_stages.py` passes with the run record asserting the bumped version.
5. `uv run clutch meta check clutch/specs/implement.md` exits 0 only if Check has written headers; Implement does not run it.

## Verification
```
./dev.py test tests/integration/test_implement_spec_premise_proof.py tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_meta_headers.py tests/integration/test_implement_spec_mutation_check.py tests/integration/test_stages.py
```

## Definition of rejected
The branch edits any step other than step 3 of the spec, forbids `premise_failed` for a real fence gap whose finding names the out-of-fence line, uses a literal version target other than the next minor above main, or leaves an old-version pin failing.

## Time budget
- expected: 12m
- stuck: 24m
