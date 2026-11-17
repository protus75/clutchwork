---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
none

## Context
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/drain-loop.md
- clutch/docs/host-authoring.md
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_ask_drain_loop.py
- tests/integration/test_ask_drain_loop_agent.py
- tests/unit/test_ask_drain_loop.py

## Goal / Why
The owner asked on 2026-11-17 that the lessons of the first plan-ticket-drain run reach the shipped prompts, so the next run on any host starts with them. Four are missing from `clutch prompt plan-ticket-drain`, `clutch prompt drain-loop` and the authoring guide:

1. Author upcoming tickets while a ticket runs. The kickoff says "Let the driver author" and "Hand-author only when the driver cannot", but the driver authors only at idle points, between tickets. Implement runs take a median of 3-6 minutes (see 4), so authoring, not running, sets the pace. The owner directed: "you can author/lint/review upcoming tickets while one is in process running".
2. Resolve a draft as soon as it appears. A draft holds one of the driver's author-ahead slots. On 2026-11-17 the drain went quiescent three times with only drafts left, because the drafts were assessed after the drain stopped, not while the previous ticket ran. `clutch confirm` and `clutch reject` already queue through a running engine's inbox.
3. Never triage the driver's own `roadmap_row` Suggestion Box messages. On 2026-11-17 a triage batch over all pending messages nearly included box-000657, the driver's author request for roadmap row 119.
4. Ticket time estimates are AI time. Owner decision 22 in `docs/roadmap.md` section 6 says the 30-minute and 60-minute limits are AI time: the actual Implement minutes on the model. On 2026-11-17 actual Implement time ran at about 0.1 of the estimate for every model, because authors had been estimating human time (codex gpt-6.1-terra: 354 runs, median estimate 30m, median actual 3.4m).

## Scope in / Scope out
In:
- `clutch/specs/ask/plan-ticket-drain.md`, `Authoring` section:
  - Replace the "Let the driver author" and "Hand-author only when the driver cannot" bullets with one rule. While a ticket runs, author the next ready rows yourself, at most the window ahead. Give each row its own agent with `clutch prompt author <stem>`, then the `clutch prompt review <stem>` audit, then confirm the ticket, so the drain never waits on authoring. The driver also authors at start and after every settle, and links a row whose ticket file already exists instead of authoring it twice.
  - Keep the window rule (4, or 2 after a drift failure), the Depends-on rule and the "never hold or stop a drain" rule.
- The same file, `Supervising` section, gains two bullets:
  - Resolve a draft the tick it appears, while the engine runs: run `clutch prompt drafts` and execute its Recommendation. An unresolved draft holds a slot of the driver's author-ahead window and stalls the drain into quiescence.
  - Never triage a `roadmap_row` Suggestion Box message; the driver owns it. Pass `clutch triage` only the ids of other message classes.
- `clutch/specs/ask/drain-loop.md`: one sentence in its drafts step saying a draft is resolved the tick it appears, even while an engine runs, because confirm and reject queue through the engine's inbox. One sentence in its Suggestion Box step saying a `roadmap_row` message is never triaged or dismissed.
- `clutch/docs/host-authoring.md`, the `Time budget` bullet: add that `expected` and `stuck` are AI time, the actual Implement minutes on the model that runs the ticket, never human working time.
- Tests that pin the changed text:
  - `tests/integration/test_ask_plan_drain.py::test_plan_ticket_drain_prompt_content`: drop `Let the driver author` from its phrase list, and add `while a ticket runs`, `the tick it appears` and `roadmap_row`.
  - `tests/integration/test_ask_drain_loop.py`, `tests/integration/test_ask_drain_loop_agent.py` and `tests/unit/test_ask_drain_loop.py`: update only the assertions that pin drain-loop text this change edits.

Out: the engine code, CORE_TEMPLATE, the author and review prompts, `docs/roadmap.md`, and estimate calibration (roadmap row 142).

## Scope fence
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/drain-loop.md
- clutch/docs/host-authoring.md
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_ask_drain_loop.py
- tests/integration/test_ask_drain_loop_agent.py
- tests/unit/test_ask_drain_loop.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_ask_plan_drain.py` exits 0. The rendered kickoff contains `while a ticket runs`, `the tick it appears` and `roadmap_row`, and no longer contains `Let the driver author` or `Hand-author only when the driver cannot`. Ruled out: a kickoff that still leaves authoring to the driver's idle points.
2. `./dev.py test tests/integration/test_ask_drain_loop.py tests/integration/test_ask_drain_loop_agent.py tests/unit/test_ask_drain_loop.py` exits 0, and `uv run clutch prompt drain-loop` prints text containing `the tick it appears` and `roadmap_row`. Ruled out: a drain-loop prompt that still waits for quiescence to resolve drafts or lets triage take the driver's messages.
3. `clutch/docs/host-authoring.md`'s `Time budget` bullet says `expected` and `stuck` are AI time, the actual Implement minutes on the model, which a reader can check in that bullet. Ruled out: a guide that leaves the estimate's unit open, which produced human-time estimates about ten times the actual run.
4. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/integration/test_ask_plan_drain.py tests/integration/test_ask_drain_loop.py tests/integration/test_ask_drain_loop_agent.py tests/unit/test_ask_drain_loop.py
./dev.py test
```

## Definition of rejected
The branch is rejected if it changes engine code, CORE_TEMPLATE, the author or review prompts, or any file outside `## Scope fence`; if it removes the window, Depends-on or never-hold-the-drain rules from the kickoff; or if it weakens a test beyond the phrase and assertion updates named in Scope in.

## Time budget
- expected: 10m
- stuck: 20m
