---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- gemini-provider

## Runs before
- training-export-ship-gate

## Context
- clutch/docs/host-authoring.md#What each section is for
- tests/integration/test_precondition_rules.py
- tickets/gemini-provider/ticket.md#Scope in / Scope out

## On-demand
- clutch/specs/requisition_review.md

## Goal / Why
After this ticket, requisition review raises a `snag` with code `deferred-to-person` on a ticket that leaves work to an operator, owner, user or person and names no existing ticket stem or fenced roadmap row that delivers it. The finding's paved road: name that stem in backticks, add a fenced follow-up roadmap row, or fence the file and put the edit in Scope in. The authoring guide's deferral sentence says the same.

Why: `gemini-provider` said "Routing gemini in this repo's `config.yaml` stays an operator edit after setup" in Scope in / Scope out and forbade a `config.yaml` change. Roadmap decision 19 has no person in the loop, so that edit never happened. The installed gemini CLI went unchecked and stale (0.49.0 against 0.70.0), and a plan was then written on a stale capture. The guide already requires an existing stem or fenced roadmap row for "work deferred to separate tickets", and it forbids "a precondition that a person must perform". A deferral phrased as someone else's later edit fits neither sentence, and requisition review has no rule for it. A lint word list would be a denylist, which CLAUDE.md "Fail closed" forbids, so the rule goes in the LLM review.

## Boundary contract
### Requisition review rules
- disposition: extend
- owner: clutch/specs/requisition_review.md
- consumers: the requisition review stage and `clutch ticket review`
- observable change: one more Task bullet that snags a deferral of work to a person with no delivering stem or fenced roadmap row
- compatibility: every existing rule bullet is unchanged; the reply schema is unchanged (`snag` findings already carry a free code)
- acceptance: the rendered Task section contains the new rule text
- tests: tests/integration/test_deferral_rules.py
- post-merge source of truth: clutch/specs/requisition_review.md

## Scope in / Scope out
Scope in:
- `clutch/specs/requisition_review.md`: add one Task bullet after the repo-state precondition bullet, containing these sentences verbatim: "A ticket that leaves work to an operator, owner, user, or person, or to a later setup step, and names no existing ticket stem in backticks or fenced follow-up roadmap row that delivers it: raise a `snag` with code `deferred-to-person`." and "Paved road: name the delivering ticket stem in backticks, add a fenced follow-up roadmap row, or fence the file and put the edit in Scope in." Bump `version` to the next minor above its version on main.
- `clutch/docs/host-authoring.md`: in `What each section is for`, extend the `Scope in / Scope out` sentence "Work deferred to separate tickets needs an existing ticket stem in backticks or a fenced follow-up roadmap row." so it also covers work left to an operator, owner, user, person or later setup step, which needs the same, because no person runs the pipeline. Nothing else in the guide changes.
- `tests/unit/test_specs.py` and `tests/integration/test_specs_delimiter_note.py`: update the `requisition_review` version pin to the bumped version. Nothing else in either file changes.
- New `tests/integration/test_deferral_rules.py`: render the spec the way `tests/integration/test_precondition_rules.py::task_section` does (a local copy of that helper, not an import) and assert that both sentences above are in the Task section.

Scope out:
- A lint word list or any code change in `clutch/tickets.py`.
- Editing `tickets/gemini-provider/ticket.md` (merged history). The instance fix is `gemini-provider-configured`.

## Scope fence
- clutch/specs/requisition_review.md
- clutch/docs/host-authoring.md
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_deferral_rules.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_deferral_rules.py` exits 0. It fails if either sentence is missing from the rendered Task section of `clutch/specs/requisition_review.md` (for example, a spec that has only the old precondition bullet).
2. `./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_precondition_rules.py` exits 0. The version pins match the bumped spec, and every existing precondition rule string is still rendered.
3. The `uv run python -c` command in `## Verification` exits 0: `clutch/docs/host-authoring.md` contains `no person runs the pipeline` and still contains `Work deferred to separate tickets`.

## Verification
```
./dev.py test tests/integration/test_deferral_rules.py tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_precondition_rules.py
uv run python -c "import pathlib; t = pathlib.Path('clutch/docs/host-authoring.md').read_text(); assert 'no person runs the pipeline' in t and 'Work deferred to separate tickets' in t"
```

## Definition of rejected
- an existing requisition review Task bullet is removed or reworded;
- `clutch/tickets.py` or any lint code changes;
- the spec version is set to anything other than the next minor above main.

## Time budget
- expected: 10m
- stuck: 20m
