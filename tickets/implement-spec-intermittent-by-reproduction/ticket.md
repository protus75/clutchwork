---
state: confirmed
source: box:suggestion
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- tickets/implement-spec-intermittent-not-premise/ticket.md

## Goal / Why
An Implement run whose only remaining failure is one non-reproducing flake replies `ok` and records a second problem. It does not end `premise_failed`.

Today the intermittent-failure paragraph in `clutch/specs/implement.md` applies only when "no changed file is imported, called or exercised by that test". Nearly every integration test imports `clutch/__main__.py`, so any ticket that edits it can never use the exception. Incident 2026-11-16: `roadmap-accept` attempt 0 parked `premise_failed` on one failure of `tests/integration/test_kill_cli_activation.py::test_killed_run_is_terminal_or_restart_reconcilable[True]`. That test passed alone, passed on base, and passed in two earlier full candidate runs. The diagnosis verdict was retry, but the diff was lost and the stem is parked until someone edits the ticket. The open ticket `runner-terminal-removal-survives-kill` fixes only that one flaky test, not the spec rule.

The new rule judges by reproduction, not by import reach: a failure that passes on the base commit, passes alone on the candidate, and does not reproduce on one further full `## Verification` run is intermittent. A failure that reproduces on either rerun stays `premise_failed`.

## Scope in / Scope out
Scope in:
- In `clutch/specs/implement.md`, rewrite the paragraph that starts "When a failing test passes on the base commit and fixing it would require an edit outside `## Scope fence`", and the two sentences after it that depend on it.
  - The paragraph requires an isolated rerun on the candidate and exactly one further full run of the ticket's `## Verification` command.
  - If the test passes alone and the further full run does not reproduce the failure, the failure is intermittent: commit, reply `ok`, and report it in `second_problems` and `surprises`.
  - Remove the "no changed file is imported, called or exercised by that test" condition.
  - Keep the sentence that this paragraph overrides step 2's base-failure requirement for this case only.
  - Replace "One isolated rerun is the only evidence; never rerun the full suite until it passes and count that as proof." with a sentence saying the isolated rerun and the one further full run are the only evidence, and that further reruns until green are never proof.
  - Replace the closing sentence so a failure that reproduces on the isolated rerun or on the further full run stays a `premise_failed` finding.
- Bump the `version` of `clutch/specs/implement.md` to the next minor above the version on main.
- In `tests/unit/test_specs.py`, update the pinned version in both places that pin the implement spec version, and update the exact-text assertions of the rewritten paragraph and its dependent sentences.
- In `tests/integration/test_implement_spec_mutation_check.py` and `tests/integration/test_stages.py`, update only the pinned implement spec version string.

Scope out:
- No change to engine code, other specs, or the flaky test itself (owned by `runner-terminal-removal-survives-kill`).
- No change to the base-failure rule that precedes the paragraph.

## Scope fence
- clutch/specs/implement.md
- tests/unit/test_specs.py
- tests/integration/test_implement_spec_mutation_check.py
- tests/integration/test_stages.py

## On-demand
- clutch/specs/implement.md
- tests/unit/test_specs.py

## Acceptance criteria
1. `tests/unit/test_specs.py` asserts that the implement spec task text contains the new paragraph, including the requirement of one further full `## Verification` run. It also asserts that the text does not contain "no changed file is imported, called or exercised by that test". `./dev.py test tests/unit/test_specs.py` fails on the old text, not only on the new.
2. `tests/unit/test_specs.py` asserts that the text keeps the sentence that the paragraph overrides step 2 for this case only, and that a failure reproducing on the isolated rerun or on the further full run stays a `premise_failed` finding. A spec that drops either sentence fails `./dev.py test tests/unit/test_specs.py`.
3. The `version` in `clutch/specs/implement.md` is the next minor above the version on main. Every test that pins the implement spec version expects that value, and `./dev.py test tests/integration/test_implement_spec_mutation_check.py tests/integration/test_stages.py` exits 0, not failing on a stale `2.15`.

## Verification
```
./dev.py test tests/unit/test_specs.py tests/integration/test_implement_spec_mutation_check.py tests/integration/test_stages.py
```

## Definition of rejected
The rewritten paragraph still conditions the intermittent exception on whether a changed file is imported, called or exercised by the test. Or it lets a failure that reproduces on a rerun reply `ok`. Or it accepts rerunning the suite until it passes as proof. Or the diff edits anything outside the fence.

## Time budget
- expected: 20m
- stuck: 45m
