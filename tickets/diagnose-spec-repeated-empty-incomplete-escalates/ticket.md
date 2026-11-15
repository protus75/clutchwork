---
state: draft
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
- tests/unit/test_specs.py::test_diagnose_spec_states_attempt_starting_point

## On-demand
- chupa/specs/diagnose.md

## Goal / Why
`chupa/specs/diagnose.md` defines `escalate` as 'the approach was sound but needs more capability' and `split` as a size problem. It says nothing about an `incomplete` terminal with an empty diff. In vscode-help-registry, codex quit with an empty diff three times at about $1 each. Diagnose chose `retry`, then `split`, then `retry` again. The 'begin editing early' lesson was ignored on the next attempt, and the ticket ended in the Reject queue. Its parent, vscode-help, had already quit the same way on three attempts. After this change the spec tells Diagnose to choose `escalate` for a repeated empty-diff `incomplete` quit. A first such quit still gets `retry`, and `split` stays for a diff-budget or boundary limit the run record names.

## Scope in / Scope out
Scope in:
- Add one paragraph to the `## Task` section of `chupa/specs/diagnose.md`, after the base-commit measurement paragraph. It says: when the terminal is `incomplete` with an empty diff, and the run record shows an earlier attempt of this ticket, or of the parent it was split from, that also ended `incomplete` with an empty diff, choose `escalate`, not `retry` or `split`, because lessons to start editing have already failed. A first empty-diff `incomplete` still gets `retry`. `split` stays for a run record that names a diff-budget or boundary limit the attempt actually hit.
- Bump the spec `version` to the next minor above the version on main.
- In `tests/unit/test_specs.py`, update only the `diagnose` version pin in `test_spec_lint_accepts_the_implement_and_requisition_specs` to that bumped version.
- Create `tests/integration/test_diagnose_spec.py`. It reads `chupa/specs/diagnose.md` and pins the new paragraph's sentences. A unit test must not read disk, so this test lives under `tests/integration/`.

Scope out:
- Provider routing or render-size ceilings; decision declined-box-000443 covers those.
- The diagnose eval corpus. `tests/integration/test_diagnose_eval.py` asserts the corpus holds 12 fixtures, so no fixture is added.
- Other diagnose spec rules, which have their own tickets.
- Rule home: this is a chupa engine prompt spec, so the rule lives in the spec and is not copied to host files.

## Scope fence
- chupa/specs/diagnose.md
- tests/unit/test_specs.py
- tests/integration/test_diagnose_spec.py

## Acceptance criteria
1. The rendered `## Task` of `chupa/specs/diagnose.md` contains the whole-sentence rule that an `incomplete` terminal with an empty diff, after an earlier attempt of this ticket or of its split parent also ended `incomplete` with an empty diff, gets `escalate`, not `retry` or `split`. `./dev.py test tests/integration/test_diagnose_spec.py` checks the exact sentences with a new test, which fails if the paragraph is removed.
2. The same new test in `tests/integration/test_diagnose_spec.py` asserts the first-occurrence guard is present: a first empty-diff `incomplete` still gets `retry`. It fails if that guard sentence is dropped.
3. The same new test in `tests/integration/test_diagnose_spec.py` asserts the `split` carve-out is present: `split` stays for a run record that names a diff-budget or boundary limit the attempt hit. It fails if that sentence is dropped.
4. The `diagnose` version in `chupa/specs/diagnose.md` is the next minor above its version on main, and the pin in `test_spec_lint_accepts_the_implement_and_requisition_specs` equals it. `lint_spec(text) == []` still holds, so the spec's size budget is respected.
5. The existing `test_diagnose_spec_lesson_length_guidance` and `test_diagnose_spec_states_attempt_starting_point` still pass unchanged.

## Verification
```
./dev.py test tests/integration/test_diagnose_spec.py
./dev.py test tests/unit/test_specs.py
```

## Definition of rejected
The branch is rejected if it makes a first empty-diff `incomplete` escalate, removes the `split` carve-out, edits any file outside the fence, adds a diagnose eval fixture, adds a disk-reading test to `tests/unit/`, or pins the new paragraph with a test that still passes when the paragraph is deleted.

## Time budget
- expected: 15m
- stuck: 40m
