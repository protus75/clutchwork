---
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
source: box:roadmap_row
state: confirmed
---

## Depends on
none

## Context
- docs/boundary-contract-plan.md#Proposed ticket content
- docs/boundary-contract-plan.md#Exceptions and preservation claims
- docs/boundary-contract-plan.md#Rollout

## Goal / Why
Roadmap row 150. `docs/boundary-contract-plan.md` gains a `## Trial results` section recording a hand application of the proposed boundary-contract form to 10-20 merged tickets under `tickets/`. The sample covers every Phase 0 category the plan lists: seam reuse, a justified new seam, CLI behavior, configuration or a closed vocabulary, a persisted or journal format, extension snapshot data, a private bug fix, a boundary-preserving refactor, a documentation-only change, generated output, and a sibling-ticket contract dependency. At least two entries use a preservation claim and at least two name a sibling dependency. The section records, per ticket: the stem, its category, the form as applied, and any author disagreement. It then records where the form became boilerplate, what facts review actually needed, which fields were consistent enough to lint, the chosen section name, closed dispositions, required fields, earning conditions and `none` reasons, and baseline findings (mistakes the form would have caught in the historical tickets). Later tickets (`boundary-contract-authoring`, `boundary-contract-lint`) take their exact grammar from this evidence, so it must exist before them.

## Scope in / Scope out
In: add one `## Trial results` section to `docs/boundary-contract-plan.md`, placed immediately after the `## Rollout` section and before `## Measures of success`, at a real section boundary and never inside a decision or its example block. Where a trial result differs from an owner decision recorded in the plan, record it as a disagreement and leave the decision text unchanged. Also edit the plan's `## Status` text only to say the trial is done, and reword only the intro paragraph that says the retrospective trial still chooses the exact closed Markdown grammar (near the top of the file) so it says the trial has chosen the grammar and points to `## Trial results`.
Out: engine code, tests, skeletons, the authoring guide, specs, `docs/roadmap.md` (the driver strikes the row), and the edited historical tickets (the trial applies the form on paper only; no existing ticket changes). No other plan text changes.

## Scope fence
- docs/boundary-contract-plan.md

## Acceptance criteria
1. `docs/boundary-contract-plan.md` contains exactly one heading line `## Trial results`, checked with `grep -c '^## Trial results$' docs/boundary-contract-plan.md` printing `1`, not `0`.
2. The `## Trial results` section lists between 10 and 20 distinct ticket stems, each one a directory under `tickets/`, checked by reading `docs/boundary-contract-plan.md#Trial results` against `tickets/`.
3. Every one of the eleven Phase 0 categories in `docs/boundary-contract-plan.md#Rollout` is named in the section with at least one stem, checked by reading `docs/boundary-contract-plan.md#Trial results`.
4. The section has subheadings `### Disagreements`, `### Chosen grammar` and `### Baseline findings`, checked with `grep -c '^### \(Disagreements\|Chosen grammar\|Baseline findings\)$' docs/boundary-contract-plan.md` printing `3`, not a smaller count.
5. `### Chosen grammar` states the section name, the closed disposition list, the required fields, the earning conditions and the `none` reasons, checked by reading `docs/boundary-contract-plan.md#Chosen grammar`.
6. The `## Trial results` heading sits at a section boundary: the line before it is not inside a fenced code block and `### 13. How short should the none preservation form be?` with its example block is byte-identical to main, checked with `git diff main -- docs/boundary-contract-plan.md` showing no removed or changed line inside that decision.
7. The intro paragraph no longer says the trial still chooses the grammar, checked with `grep -c 'trial still chooses' docs/boundary-contract-plan.md` printing `0`, not `1`.
8. `uv run clutch ticket lint boundary-contract-trial` exits 0 and no file other than `docs/boundary-contract-plan.md` differs from main, checked with `git diff --name-only main`.

## Verification
```
uv run clutch ticket lint boundary-contract-trial
./dev.py test tests/unit/test_roadmap_table.py
```

## Definition of rejected
A branch that edits any file besides `docs/boundary-contract-plan.md`, changes an owner decision's text, places `## Trial results` inside a fenced block or a decision, omits any Phase 0 category, or fills the section with invented ticket stems that do not exist under `tickets/`.

## Time budget
- expected: 15m
- stuck: 30m
