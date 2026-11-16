---
state: draft
source: box:suggestion
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- tests/unit/test_specs.py::test_spec_lint_accepts_the_implement_and_requisition_specs

## On-demand
- clutch/specs/implement.md

## Goal / Why
After this change `clutch/specs/implement.md` tells Implement that the per-assertion mutation check (the paragraph beginning "For each assertion, name the likely wrong implementation") is part of the work and is finished before replying. An unfinished mutation check is never a reason to reply `incomplete` when every `## Verification` command passes. Instead the agent finishes the remaining checks, restores the code, commits, and replies `ok`.

Why: on 2026-11-16 two attempts were thrown away for the same cause. Each cost a full Implement call and a retry draw. The Diagnose records name the mutation-check step, not wrong code or a wrong ticket:
- `release-verb` attempt 0 stopped after about 5 of 60 minutes with all 7 fenced files uncommitted.
- `roadmap-table-parser` attempt 1 passed every Verification command at 98.7% coverage of `clutch/roadmap.py`, checked one mutation, and replied `incomplete`.

The spec defines `incomplete` as "stopped before finished work was committed" and added the mutation step in `implement-spec-assertion-masking-check`, but never says the step must be finished before replying. Measure after merge: count `incomplete` Implement terminals in `tickets/*/diagnosis.json` and the spools whose lessons cite unfinished mutation or wrong-implementation checks. The count should fall to zero.

The engine-side alternative (sending a committed `incomplete` branch on to Check) is out of scope. It would not have rescued `release-verb`, which had nothing committed.

## Scope in / Scope out
Scope in:
- Edit `clutch/specs/implement.md`. Add exactly this one sentence at the end of the mutation-check paragraph: "Finish the check for every assertion before replying, and if time is short, finish it and restore the code rather than stopping partway; unfinished mutation checks are never a reason to reply `incomplete`."
- In the `incomplete` bullet, add exactly this one sentence: "Never use `incomplete` because mutation checks remain while the Verification commands pass."
- Bump the spec `version` from "2.14" to the next minor above the version on main.
- Update two version pins in `tests/unit/test_specs.py` to the bumped version: the `("implement", "2.14")` pin in `test_spec_lint_accepts_the_implement_and_requisition_specs`, and the `spec.meta.version == "2.14"` assertion in `test_implement_spec_consumer_read` (line 127). Those two pins are the only expectations that change in that file.
- Add a new test file that pins the new sentences.

Scope out:
- No engine code change.
- No change to `diagnose.md` or to how Diagnose escalates (`diagnose-spec-repeated-empty-incomplete-escalates` covers that).
- No change to the mutation-check wording beyond the added sentence.

## Scope fence
- clutch/specs/implement.md
- tests/unit/test_specs.py
- tests/integration/test_implement_spec_mutation_check.py

## Acceptance criteria
1. `clutch/specs/implement.md` carries the two exact sentences named in Scope in: one at the end of the mutation-check paragraph and one in the `incomplete` bullet. `tests/integration/test_implement_spec_mutation_check.py` asserts both exact sentences are present. The test fails on the current spec, which has neither.
2. The spec `version` is the next minor above 2.14. `tests/integration/test_implement_spec_mutation_check.py` asserts the parsed front matter version equals that value, not "2.14".
3. `tests/unit/test_specs.py::test_spec_lint_accepts_the_implement_and_requisition_specs` and `tests/unit/test_specs.py::test_implement_spec_consumer_read` both pass with the bumped version (neither asserts "2.14"), and `lint_spec` returns no findings for the edited spec.
4. The new test fails when the `incomplete` bullet sentence is removed from the spec, which rules out a test that checks only the mutation paragraph. The implementer applies this removal once, confirms the failure, and restores the file.

## Verification
```
./dev.py test tests/unit/test_specs.py tests/integration/test_implement_spec_mutation_check.py
```

## Definition of rejected
The branch changes engine code, edits `diagnose.md`, rewrites the mutation-check paragraph beyond one added sentence, leaves the version unbumped, or adds a test that passes on the unedited spec.

## Time budget
- expected: 15m
- stuck: 40m
