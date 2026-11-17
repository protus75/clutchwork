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
- tests/integration/test_ask_plan_drain.py
- tests/unit/test_ask_plan_drain.py

## Goal / Why
The owner, 2026-11-17: the plan-ticket-drain agent must surface, before it starts, any contradiction between its delegation and the host's own rules. In this repo's first run the delegation said to carry out the ticket edits a `clutch prompt diagnose` or `clutch prompt drafts` Recommendation names, while the host's agent conduct files say a supervising session may not rewrite a ticket the engine authored. The agent found that only mid-run, when a permission check refused the rewrite of two engine-authored tickets (`supervise-every-route` and `test-gate-floors-measured`). Both held the roadmap driver's two author-ahead slots, so the drain went quiescent with 14 rows ready and waited on the owner. A run with no person in the loop has to clear every such conflict up front, the same way it reports a missing credential.

After this change `clutch prompt plan-ticket-drain` does two things. First, before any engine starts, it has the agent read the host's agent conduct files, list every rule that forbids an action the delegation needs, quote each one to the owner once, and get an explicit override before the run starts. Second, its delegation names the ticket edits a Recommendation calls for, including narrowing or repairing a ticket the engine authored.

## Scope in / Scope out
In:
- `clutch/specs/ask/plan-ticket-drain.md`, `Before you start`: a new first bullet. Before any other step and before any engine starts, read the host's agent conduct files (the files its agents load as standing instructions). List every rule there that forbids an action this delegation needs: confirming or rejecting, carrying out the ticket edits a Recommendation names (including narrowing or repairing a ticket the engine authored), writing roadmap rows, and stopping or restarting the engine. Quote each such rule to the owner once, in one message, and start only after the owner gives an `explicit override` for each one. A conflict found mid-run means this check was skipped.
- The same file, `Delegation`: a new bullet. The owner's delegation covers the ticket edits a Recommendation names, including narrowing or repairing a ticket the engine authored. A host conduct rule that forbids them is a conflict for the first `Before you start` bullet.
- `tests/integration/test_ask_plan_drain.py::test_plan_ticket_drain_prompt_content`: the phrase list gains `conduct files`, `explicit override` and `the engine authored`, and the test asserts the first `conduct files` comes before the first `clutch doctor`.

Out: the drain-loop, diagnose, drafts, box, running, author and review prompts; CORE_TEMPLATE, the host conduct files themselves, and `docs/roadmap.md`. Naming a provider or a specific conduct file name in the prompt is out: `test_prompts_carry_no_session_facts` forbids provider names.

## Scope fence
- clutch/specs/ask/plan-ticket-drain.md
- tests/integration/test_ask_plan_drain.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_ask_plan_drain.py` exits 0. In it, `test_plan_ticket_drain_prompt_content` finds `conduct files`, `explicit override` and `the engine authored` in the rendered kickoff, and fails if the first `conduct files` comes after the first `clutch doctor`. Ruled out: a kickoff that checks host rules only after the run starts, or never.
2. `./dev.py test tests/integration/test_ask_plan_drain.py tests/unit/test_ask_plan_drain.py` exits 0 with every other existing assertion unchanged, including `test_prompts_carry_no_session_facts` and `test_prompts_name_only_existing_verbs`. Ruled out: a new bullet that names a provider, a machine path, or a verb that does not exist.

## Verification
```
./dev.py test tests/integration/test_ask_plan_drain.py tests/unit/test_ask_plan_drain.py
```

## Definition of rejected
The branch is rejected if it edits a file outside `## Scope fence`, removes or weakens an existing assertion in `tests/integration/test_ask_plan_drain.py`, or places the conduct-file check anywhere but first in `Before you start`.

## Time budget
- expected: 15m
- stuck: 40m
