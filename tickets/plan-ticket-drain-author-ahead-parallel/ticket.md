---
state: draft
source: human
priority: P0
kind: chore
---

## Depends on
- none

## Context
- clutch/specs/ask/plan-ticket-drain.md
- tests/integration/test_ask_plan_drain.py::test_plan_ticket_drain_prompt_content

## Goal / Why
An operator running `clutch prompt plan-ticket-drain` authors the next roadmap rows in parallel while a ticket is implemented, so the engine's driver never has to author a row inline and the next confirmed ticket is never kept waiting behind authoring. Today the prompt leaves authoring to the driver ("The driver also authors at start and after every settle") and to `clutch roadmap author --ahead` between drains. The driver's author pass runs serially between tickets: drain runs it after every settle before selecting the next ticket (`clutch/drain.py`, the `_run_driver` call in `run`), and serve admits no ticket while `driver_pending()` holds (`clutch/serve.py`). On 2026-11-19 a supervising session that left authoring to the driver saw `graphics-kind` authored and requisition-reviewed while `document-agent-roadmap-prompt`, `graphics-kind` and `conflict-rerun-accounting` sat confirmed and waiting. The owner called the run "so shitty slow". The prompt also has the operator wait up to about 25 minutes between ticks, so a draft or a Reject-queue stem can sit idle for most of that time.

## Boundary contract
### Plan-ticket-drain operator prompt
- disposition: extend
- owner: clutch/specs/ask/plan-ticket-drain.md
- consumers: `clutch prompt plan-ticket-drain` (clutch/ask.py renders it verbatim), operator sessions that run it, tests/integration/test_ask_plan_drain.py
- observable change: the Authoring section makes the operator keep the author-ahead window full with one parallel agent per ready row while a ticket runs, starting before the first drain, so the driver links rows instead of authoring them; it forbids `clutch roadmap author --ahead` as the way to fill the window; the Supervising section reacts to engine state changes as they happen instead of waiting up to about 25 minutes per tick
- compatibility: every other rule, phrase and section order the existing test pins stays; the prompt remains unversioned and is still rendered by the same verb
- acceptance: the updated phrase test passes and the removed slow instructions are absent
- tests: tests/integration/test_ask_plan_drain.py
- post-merge source of truth: clutch/specs/ask/plan-ticket-drain.md

## Scope in / Scope out
Scope in, all in `clutch/specs/ask/plan-ticket-drain.md`:
- Authoring: replace the first bullet's serial wording with: before the first drain starts and whenever a ticket is running, author every ready row up to the window at once, one agent per row running in parallel (each with `clutch prompt author <stem>`, then a separate `clutch prompt review <stem>` audit agent, then lint, review and confirm as today). State why: the driver's author pass runs between tickets and holds up the next dispatch, so the operator's job is to leave it nothing to author; the driver then only links rows whose ticket already exists. Keep the phrases `while a ticket runs`, `clutch prompt author` and `clutch prompt review`.
- Authoring: replace "Between drains, top up with `clutch roadmap author --ahead <window>` (it takes the writer lock)." with a sentence saying never to fill the window with `clutch roadmap author --ahead`, because it takes the writer lock and authors serially; fill it with parallel agents instead, also between drains. Keep the window size rules (4, or 2 after a drift failure) and the Depends on rule unchanged.
- Authoring: keep "Authoring overlaps the running drain: never hold or stop a drain for it."
- Supervising: replace "Between ticks wait with your agent's loop or wait facility until the engine exits or about 25 minutes pass." with: watch this checkout's engine state with the agent's monitor or wait facility and act on each change as it happens (a merge or settle, a new in-flight stem, a draft, a Reject-queue stem, the engine exiting), so new authoring starts the moment a ticket dispatches; fall back to a timed check only when no change arrives.
- `tests/integration/test_ask_plan_drain.py::test_plan_ticket_drain_prompt_content`: add the phrases `in parallel` and `before the first drain` to the pinned list, and add `assert "about 25 minutes" not in text` and `assert "top up with" not in text`. Change nothing else in that file.

Scope out: the engine's driver scheduling in `clutch/drain.py` and `clutch/serve.py` (a separate engine change), the drain-loop ask prompt, the author and review ask prompts, the window size, and every other section of the prompt.

## Scope fence
- clutch/specs/ask/plan-ticket-drain.md
- tests/integration/test_ask_plan_drain.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_ask_plan_drain.py` passes with the pinned phrase list extended by `in parallel` and `before the first drain`, so a prompt that still leaves authoring to the driver fails it.
2. The same test asserts `about 25 minutes` and `top up with` are absent from the rendered prompt, so a prompt that still waits up to 25 minutes per tick or fills the window with `clutch roadmap author` fails it.
3. Every phrase and ordering the test pinned before this change still passes, including `while a ticket runs`, `clutch roadmap author --ahead`, `never hold`, and `clutch prompt drain-loop`; checked by `./dev.py test tests/integration/test_ask_plan_drain.py tests/unit/test_ask_plan_drain.py tests/integration/test_ask.py`.

## Verification
```
./dev.py test tests/integration/test_ask_plan_drain.py tests/unit/test_ask_plan_drain.py tests/integration/test_ask.py
```

## Definition of rejected
The prompt still tells the operator to leave authoring to the driver, to fill the window with `clutch roadmap author --ahead`, or to wait up to about 25 minutes between ticks; any section other than Authoring and Supervising changes; or any test other than `test_plan_ticket_drain_prompt_content` changes.

## Time budget
- expected: 10m
- stuck: 20m
