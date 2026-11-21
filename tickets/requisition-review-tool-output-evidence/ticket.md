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
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_requisition_review_stand_in_closure.py

## On-demand
- clutch/specs/requisition_review.md

## Goal / Why
Requisition review raised snags on the five meta-annotate shards at least eight times (codes `format-gate-contradiction`, `format-breaks-block-placement`, `premise`). Each rested on a prediction that `ruff format` would add a blank line between a module docstring and the `# clutch:meta` block. No reviewer ran ruff; one snag reasoned from black's source and overruled the manual ruff run cited in the ticket. All five shards merged with ruff-fix, ruff-format, format and integration green, so every snag was false and cost rounds, rewrites and an author detour.

After this ticket, `clutch/specs/requisition_review.md` carries a rule: a finding that depends on what a formatter, linter, parser or CLI outputs must cite a run of that tool on a scratch copy outside the checkout, with the command and its result. A prediction from reading the tool's source, or one that contradicts a run the ticket cites, is never a snag. If the tool cannot be run, the doubt goes in `summary` and the verdict rests on the other findings. The rule applies only to findings that depend on a tool's output, and the run happens only in a scratch copy, never in the shared checkout.

Class prevention: this spec rule is the change that stops the class. Measurement after merge (not a test): in later retro windows, count requisition snags whose tool-behavior claim has no cited run or is disproved by a later green Check; expect zero.

## Boundary contract
### Requisition review prompt spec
- disposition: extend
- owner: clutch/specs/requisition_review.md
- consumers: the requisition review stage that renders this spec, and the spec tests that pin its version
- observable change: one new rule in `## Task` on evidence for tool-output findings; `version` bumps to the next minor above the version on main
- compatibility: reply schema, verdict vocabulary, input blocks and every existing rule are unchanged
- acceptance: the spec lints clean, loads, and its rendered Task contains the new rule with the three clauses (cited scratch-copy run, source-reading prediction is not a snag, unrunnable tool goes in summary)
- tests: a new integration test reading the spec, plus the two updated version pins and the updated bullet count
- post-merge source of truth: clutch/specs/requisition_review.md

## Scope in / Scope out
Scope in:
- Add one bullet to the `## Task` list in `clutch/specs/requisition_review.md` stating the rule above, including that the run happens in a scratch copy outside the checkout, never in the shared checkout, and that the rule applies only to findings whose claim depends on a tool's output. Bump `version` to the next minor above the version on main.
- Update the version pin `("requisition_review", "3.25")` in `tests/integration/test_specs_delimiter_note.py` and `("requisition_review", "3.25")` in `tests/unit/test_specs.py` to the new version; no other expectation in those files changes.
- In `tests/integration/test_requisition_review_stand_in_closure.py`, change the bullet count at line 21 from 18 to 19, with no other change to that file.
- Add `tests/integration/test_requisition_review_tool_output_evidence.py`, which reads the spec through a `Path(__file__)` anchor, follows the pattern of `tests/integration/test_requisition_review_stand_in_closure.py`, and asserts the rule's clauses.
- Keep the meta blocks of edited and new test files consistent with `uv run clutch meta check`.

Scope out: other specs, review.md, the code that renders specs, any reviewer tooling or sandboxing, and any lint that checks findings for cited runs.

## Scope fence
- clutch/specs/requisition_review.md
- tests/integration/test_specs_delimiter_note.py
- tests/unit/test_specs.py
- tests/integration/test_requisition_review_stand_in_closure.py
- tests/integration/test_requisition_review_tool_output_evidence.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_requisition_review_tool_output_evidence.py` passes; it asserts the rendered `## Task` contains the scratch-copy-outside-the-checkout run requirement, the clause that a source-reading prediction is never a snag, and the clause that an unrunnable tool's doubt goes in `summary`. A spec lacking the scratch-copy clause fails it.
2. `./dev.py test tests/integration/test_requisition_review_tool_output_evidence.py` also passes an assertion that the rule is limited to findings that depend on a tool's output; a spec that tells reviewers to run tools for every finding fails it.
3. `./dev.py test tests/integration/test_specs_delimiter_note.py tests/unit/test_specs.py` passes with the pins at the bumped version; a version left at `3.25` fails them.
4. `./dev.py test tests/integration/test_requisition_review_stand_in_closure.py` passes with the bullet count at 19, not 18.
5. `lint_spec` on `clutch/specs/requisition_review.md` returns `[]`, checked by `./dev.py test tests/integration/test_requisition.py`.
6. `uv run clutch meta check` exits 0.

## Verification
```
./dev.py test tests/integration/test_requisition_review_tool_output_evidence.py tests/integration/test_requisition_review_stand_in_closure.py tests/integration/test_specs_delimiter_note.py tests/unit/test_specs.py tests/integration/test_requisition.py
uv run clutch meta check
```

## Definition of rejected
The rule tells reviewers to run tools inside the checkout, to run a tool for every finding, or to stop raising real tool-behavior contradictions; or any other spec, the reply schema, or existing Task rules change.

## Time budget
- expected: 12m
- stuck: 24m
