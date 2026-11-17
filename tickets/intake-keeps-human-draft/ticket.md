---
state: draft
source: box:suggestion
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/tickets.py::_intake_claims
- clutch/observe.py
- clutch/specs/ask/author.md

## Goal / Why
After this ticket, intake of a new human ticket that carries an explicit `state: draft` line keeps it `draft` and stamps only `source: human`. Today `_intake_claims` ends with `stamp(stamp(text, "source", "human"), "state", "confirmed")`, which overwrites the authored `draft`. A hand ticket still being audited therefore becomes dispatchable as soon as any intake runs. The cli-group-box incident admitted a hand ticket mid-audit, which led to edits on a running ticket, and CLAUDE.md forbids those edits. `clutch ticket new` writes `state: draft`, so a ticket made by the paved road stays draft until `clutch ticket confirm <stem>`. A new human ticket with no `state:` line is still stamped `confirmed`, as today. That keeps the many hand-written test tickets that carry no state line valid and avoids a repo-wide test rewrite. The ask author prompt cannot run `confirm` (it is on its forbidden list), so it must tell the author to name `clutch ticket confirm <stem>` for the owner once review prints approve.

## Scope in / Scope out
Scope in:
- `clutch/tickets.py::_intake_claims`: for a new stem with `source` human, stamp `source: human`; stamp `state: confirmed` only when the ticket has no `state:` line, and otherwise keep the authored `draft` or `confirmed`. Keep the refusal of states other than `draft` or `confirmed`, and reword its paved road and the docstring so neither says intake always confirms.
- `clutch/observe.py`: the status label `new: confirmed by next intake` becomes a label saying a new human ticket with `state: draft` stays draft until `clutch ticket confirm`, and one with no state line is confirmed by the next intake.
- `clutch/specs/ask/author.md`: add one line saying a reviewed ticket stays `state: draft` and that the final reply names `clutch ticket confirm <stem>` for the owner to run. If the spec carries a `version`, bump it to the next minor above the version on main.
- Flip the existing expectations that pin auto-confirm of an explicit draft: `tests/integration/test_tickets.py` (asserts at the new-stem intake commit, the intake signal body and the `t-one` main:show check, where the ticket was written with `state: draft`; each now expects `state: draft` and signal body `"state": "draft"`), `tests/unit/test_intake_plan.py` (stamped text and signal body for a draft input), `tests/integration/test_review_command.py` (the `state: confirmed` assert after review on main), `tests/integration/test_drain_admissions.py` (the drain wait on `state: confirmed`: the hand draft must stay draft and undispatched until the test runs the confirm verb), `tests/integration/test_intake_scope.py` (only if an assertion on the two new `state: draft` stems flips).
- `tests/integration/test_menu_verb_parity.py`: the `new` and `staged-new` cases write `state: draft` and leave the ticket uncommitted, and the parametrize table (lines 100-101) expects `run` on. A new explicit draft now stays draft, so `run_admission` refuses it; flip the `run` expectation to False for `new` and `staged-new` and change nothing else there.
- Update the sentence that says human intake auto-confirms in `docs/how-clutch-works.md` and `clutch/docs/host-running.md` (only that sentence or row): a new human ticket with `state: draft` is confirmed with `clutch ticket confirm`.
- A new test file pins the behavior and the prompt line.
Scope out: `confirm` verb behavior, machine-source intake, established-stem handling, tickets with no `state:` line, the `ask-author-recopy-after-review` ticket (its scratch-copy rule is unchanged), and the `runner.py` confirm stamp.

## Scope fence
- clutch/tickets.py
- clutch/observe.py
- clutch/specs/ask/author.md
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- tests/integration/test_tickets.py
- tests/unit/test_intake_plan.py
- tests/integration/test_review_command.py
- tests/integration/test_drain_admissions.py
- tests/integration/test_intake_scope.py
- tests/integration/test_menu_verb_parity.py
- tests/integration/test_intake_keeps_draft.py

## Acceptance criteria
1. Intake of a new human ticket written with `state: draft` commits text containing `state: draft` and `source: human`, not `state: confirmed`; checked by `./dev.py test tests/integration/test_intake_keeps_draft.py`.
2. Intake of a new human ticket with no `state:` line commits `state: confirmed`, not `draft` and not an absent line; checked by `./dev.py test tests/integration/test_intake_keeps_draft.py`.
3. A new human ticket authored `state: confirmed` keeps `confirmed` at intake; checked by `./dev.py test tests/integration/test_intake_keeps_draft.py`.
4. A drain run over a new human ticket written with `state: draft` does not dispatch it (no stage starts for the stem) until `clutch ticket confirm <stem>` runs, after which it is dispatched; checked by `./dev.py test tests/integration/test_drain_admissions.py`.
5. `clutch/specs/ask/author.md` contains the string `clutch ticket confirm` in a line that is not the forbidden-verbs list, and still lists `clutch ticket confirm` as forbidden for the author to run; checked by `./dev.py test tests/integration/test_intake_keeps_draft.py`.
6. The existing tests in the fenced files pass with `draft` expectations, and `tests/unit/test_specs.py` passes; checked by `./dev.py test tests/integration/test_tickets.py tests/unit/test_intake_plan.py tests/integration/test_review_command.py tests/integration/test_intake_scope.py tests/integration/test_menu_verb_parity.py tests/unit/test_specs.py`.

## Verification
```
./dev.py test tests/integration/test_intake_keeps_draft.py tests/integration/test_tickets.py tests/unit/test_intake_plan.py tests/integration/test_review_command.py tests/integration/test_drain_admissions.py tests/integration/test_intake_scope.py tests/integration/test_menu_verb_parity.py tests/unit/test_specs.py
```

## Definition of rejected
Intake still overwrites an explicit `state: draft` on a new human ticket with `confirmed`, or a new compat flag or second intake path is added, or a committed human draft is dispatched without `confirm`.

## Time budget
- expected: 30m
- stuck: 60m
