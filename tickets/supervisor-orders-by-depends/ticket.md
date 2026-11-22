---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- none

## Runs before
- claude-session-names

## Context
- tests/integration/test_ask_drain_loop.py
- tests/integration/test_ask_view_events.py

## On-demand
- clutch/specs/ask/drain-loop.md
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/plan-ticket-serve.md

## Goal / Why
Owner rule, 2026-11-21: a supervising session never leaves work waiting on a merge or on a later hand edit. In this session `training-export-ship-gate` sat "held until the ticket changes" with a plan to release it by editing it after the flaky-test fix merged, and four ticket edits were left uncommitted for the drain's next scan. The owner had to ask both times. After this ticket the shipped supervising prompts say: when a ticket must wait for another, put that stem in its `## Depends on` in the same edit (a premise or hold release goes in then, not after the merge), and commit every ticket edit immediately, by explicit path or through `clutch ticket review <stem>`. Never plan a "release after X merges" step or leave a ticket edit for the engine to pick up.

## Boundary contract
### Supervising prompts ordering rule
- disposition: extend
- owner: clutch/specs/ask/drain-loop.md, clutch/specs/ask/plan-ticket-drain.md and clutch/specs/ask/plan-ticket-serve.md
- consumers: operators and agents running `clutch prompt drain-loop`, `clutch prompt plan-ticket-drain` and `clutch prompt plan-ticket-serve`
- observable change: each rendered prompt contains the rule stated in Goal / Why, as one bullet, in the same words in all three
- compatibility: every other rule in the three prompts is unchanged
- acceptance: criterion 1
- tests: tests/integration/test_ask_depends_rule.py
- post-merge source of truth: the three prompt files

## Scope in / Scope out
Scope in:
- clutch/specs/ask/drain-loop.md: add the rule as one bullet beside the existing "For a fix needing no verdict ..." bullet.
- clutch/specs/ask/plan-ticket-drain.md and clutch/specs/ask/plan-ticket-serve.md: add the same bullet next to "If a decline shows the row itself is wrong ...".
- New tests/integration/test_ask_depends_rule.py renders each prompt the way tests/integration/test_ask_drain_loop.py does and asserts the bullet.
Scope out:
- Engine scheduling, `## Depends on` semantics, the authoring guide, and the managed conduct block.

## Scope fence
- clutch/specs/ask/drain-loop.md
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/plan-ticket-serve.md
- tests/integration/test_ask_depends_rule.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_ask_depends_rule.py` proves all three rendered prompts contain the same bullet requiring the waiting ticket's `## Depends on` edge in the same edit and an immediate commit of every ticket edit, and none says to release a hold after a merge.

## Verification
```
./dev.py test tests/integration/test_ask_depends_rule.py tests/integration/test_ask_drain_loop.py tests/integration/test_ask_view_events.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_serve.py tests/integration/test_ask_plan_subagent_models.py tests/integration/test_box_triage_inbox.py
```

## Definition of rejected
Different wording across the three prompts, an engine change, or files outside the fence change.

## Time budget
- expected: 6m
- stuck: 12m
