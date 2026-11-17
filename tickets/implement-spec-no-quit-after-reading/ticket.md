---
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
source: box:suggestion
state: confirmed
---

## Depends on
none

## Context
- tests/integration/test_implement_spec_mutation_check.py

## On-demand
- clutch/specs/implement.md

## Goal / Why
An Implement attempt that has only read files, or that judges the change to be large, can no longer treat that as a reason to reply `incomplete`. Today the `incomplete` outcome in `clutch/specs/implement.md` forbids one misuse (mutation checks remaining while Verification passes) and no other. Since the mutation-check sentence merged on 2026-11-16, the journal shows 10 Implement `incomplete` replies on five tickets (main-verb-groups, evidence-store, evidence-envelope, supervise-every-route, supervise-at-idle-point). Each had no committed diff and named no external stop, all ran on the medium tier, and every ticket was estimated at 40 minutes or more. The latest is supervise-at-idle-point (expected 45m, with a stated reason not to split): attempt 0 left its edits uncommitted after about 250s, citing unfinished coverage, mutation checks and host checks, and attempt 1 replied `incomplete` after inspecting only (49s, empty diff, no blocker named). Each such quit spends attempt caps and Diagnose calls, and some tickets end in the Reject queue. This is the reopen evidence named in the rejection of implement-incomplete-needs-named-stop. Decisions 000443 and 000604 predate the budget lint and do not cover it. Dispatching long tickets on the high tier from the first attempt is a different fix: it adds engine routing, and this ticket does not choose it.

## Scope in / Scope out
Scope in:
- In the `incomplete` bullet of `clutch/specs/implement.md`, add one sentence: stopping after only reading, or because the change is large, is never a reason for `incomplete`; keep editing.
- Bump the spec `version` to the next minor above the version on main (2.16 on main today). Update each pin of the old version: `tests/unit/test_specs.py` (the version table at the top and the implement-text test that asserts `spec.meta.version`), `tests/integration/test_implement_spec_mutation_check.py`, and the `- spec: implement 2.16` expectation in `tests/integration/test_stages.py` (only that one expectation changes there).
- Add the presence test in a new file `tests/integration/test_implement_spec_keep_editing.py`.

Scope out: engine routing or tier selection, the Diagnose spec, any other sentence of the Implement spec, and a retro or lint check for the pattern. Check after merge: the next retro window shows no Implement `incomplete` with an empty diff and no named external stop on tickets estimated over 30 minutes.

## Scope fence
- clutch/specs/implement.md
- tests/unit/test_specs.py
- tests/integration/test_implement_spec_mutation_check.py
- tests/integration/test_stages.py
- tests/integration/test_implement_spec_keep_editing.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_implement_spec_keep_editing.py` passes. It loads `clutch/specs/implement.md` and asserts the `incomplete` bullet contains the sentence that stopping after only reading, or because the change is large, is never a reason for `incomplete`. It also asserts that the sentence is absent from the `premise_failed` bullet, so the text is not merely somewhere in the file.
2. `./dev.py test tests/unit/test_specs.py tests/integration/test_implement_spec_mutation_check.py tests/integration/test_stages.py` passes with the pins at the bumped version. A pin left at the old version fails these tests.
3. `load_spec` of `clutch/specs/implement.md` reports `meta.version` equal to the next minor above 2.16, checked by `./dev.py test tests/unit/test_specs.py`, not 2.16 and not a major bump.

## Verification
```
./dev.py test tests/unit/test_specs.py tests/integration/test_implement_spec_keep_editing.py tests/integration/test_implement_spec_mutation_check.py tests/integration/test_stages.py
```

## Definition of rejected
The branch changes anything in the Implement spec beyond the one sentence and the version bump, adds routing or tier logic, leaves any pin at the old version, or adds a test to a file outside the fence.

## Time budget
- expected: 20m
- stuck: 40m
