---
state: confirmed
source: human
priority: P0
kind: chore
---

## Depends on
- plan-ticket-drain-author-ahead-parallel

## Context
- clutch/specs/ask/plan-ticket-drain.md
- tests/integration/test_ask_plan_drain.py::test_plan_ticket_drain_prompt_content

## Goal / Why
An operator running `clutch prompt plan-ticket-drain` keeps only a few roadmap tickets authored ahead, and authors a row only when no confirmed, unmerged ticket fences a file that row will change, so every ticket is written and reviewed against the code it will actually run on. Today the prompt allows 4 confirmed and unrun tickets (2 only after a drift failure, returning to 4 after a clean drain), and it lets a row be authored while earlier unmerged tickets still change the same files. A ticket authored that early is reviewed against code that the tickets ahead of it then change, so it goes stale before it runs. On 2026-11-19 the owner saw this ("if you write too many they get fucked, since they don't have the on disk code to base themselves fully"). The same day, merge-model-resolve and reject-terminal-carries-rework-findings premise-parked on code that changed after they were reviewed, and a supervising session had 4 roadmap tickets authored ahead.

## Boundary contract
### Plan-ticket-drain authoring window
- disposition: extend
- owner: clutch/specs/ask/plan-ticket-drain.md
- consumers: `clutch prompt plan-ticket-drain` (clutch/ask.py renders it verbatim), operator sessions that run it, tests/integration/test_ask_plan_drain.py
- observable change: the window is at most 2 roadmap tickets confirmed and unrun, and 1 after any drift failure until a drain finishes with none; a row is authored only when no confirmed, unmerged ticket fences a file the row will change, and a draft authored ahead is re-reviewed with `clutch ticket review` against current main immediately before it is confirmed
- compatibility: the Depends on rule, the drift-failure definition, parallel authoring, and every other pinned phrase stay
- acceptance: the updated phrase test passes and the old window size of 4 is absent
- tests: tests/integration/test_ask_plan_drain.py
- post-merge source of truth: clutch/specs/ask/plan-ticket-drain.md

## Scope in / Scope out
Scope in, all in `clutch/specs/ask/plan-ticket-drain.md`, Authoring section only:
- Replace the window sentence ("Keep at most 4 roadmap tickets confirmed and unrun, or 2 after any drift failure ... A drain with no drift failure returns the window to 4.") with: keep at most 2 roadmap tickets confirmed and unrun, or 1 after any drift failure (keep the existing definition: a premise park, or a requisition or review snag citing code an earlier merge changed), returning to 2 only after a drain finishes with no drift failure. State why: a ticket written ahead is reviewed against code the unmerged tickets before it will change, so it goes stale before it runs.
- Add, beside the existing Depends on rule: author a row only when no confirmed, unmerged ticket fences a file the row will change; otherwise wait for that ticket to merge. Immediately before confirming a draft authored ahead, run `clutch ticket review` on it again against current main and repair its findings.
- Keep the phrases `drift failure`, `clutch roadmap author --ahead`, `while a ticket runs` and `never hold`.
- `tests/integration/test_ask_plan_drain.py::test_plan_ticket_drain_prompt_content`: add the phrases `at most 2` and `confirmed, unmerged ticket` to the pinned list, and add `assert "at most 4" not in text`. Change nothing else in that file.

Scope out: the engine driver's own author-ahead count (`AHEAD` in `clutch/roadmap.py`), the drain-loop ask prompt, the author and review ask prompts, and every other section of the plan-ticket-drain prompt.

## Scope fence
- clutch/specs/ask/plan-ticket-drain.md
- tests/integration/test_ask_plan_drain.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_ask_plan_drain.py` passes with the pinned list extended by `at most 2` and `confirmed, unmerged ticket`, so a prompt that still allows a 4-ticket window or authors over unmerged files fails it.
2. The same test asserts `at most 4` is absent from the rendered prompt, so the old window cannot come back unnoticed.
3. Every phrase and ordering the test pinned before this change still passes, including `drift failure`, `clutch roadmap author --ahead`, `while a ticket runs` and `never hold`; checked by `./dev.py test tests/integration/test_ask_plan_drain.py tests/unit/test_ask_plan_drain.py tests/integration/test_ask.py`.

## Verification
```
./dev.py test tests/integration/test_ask_plan_drain.py tests/unit/test_ask_plan_drain.py tests/integration/test_ask.py
```

## Definition of rejected
The prompt still allows more than 2 roadmap tickets confirmed and unrun, still lets a row be authored while a confirmed, unmerged ticket fences a file it changes, or changes any section other than Authoring; or any test other than `test_plan_ticket_drain_prompt_content` changes.

## Time budget
- expected: 10m
- stuck: 20m
