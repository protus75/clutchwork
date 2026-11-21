---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
- plan-ticket-serve-prompt
- plan-drain-conduct-conflicts

## Context
- tests/integration/test_ask_plan_serve.py
- tests/integration/test_ask_plan_drain.py

## On-demand
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/plan-ticket-serve.md

## Goal / Why
On 2026-11-20 an operator model ran `clutch prompt plan-ticket-serve` at the owner's request ("run and follow"). It took the first `Before you start` bullet literally: it ran status commands before reading the conduct files, stopped, and asked the owner four override questions the prompt's own text had already answered. `drain-loop.md` says it "overrides the conduct file's rule that a supervising session may not confirm or reject" and the `Delegation` section says the roadmap rows in Closing each phase are authorized, so no conflict stood. The prompt also says "nothing waits for a person" and then says to start only after an explicit override, and a literal reader cannot tell which line wins. The owner decision of 2026-11-17 (`plan-drain-conduct-conflicts`) stays: an uncovered conflict still stops the run until the owner overrides it.

After this ticket both plan prompts sort each conduct-file rule into two classes, so no reading stalls on a rule the prompt already settles:
- A rule that forbids only an action this prompt or `clutch prompt drain-loop` already delegates or excepts is covered. Running the prompt is the owner's explicit override of it; the operator lists it in one line and goes on without asking.
- Any other rule that forbids an action the delegation needs is uncovered. The operator quotes each once in a single message that ends with the question and runs nothing else until the owner answers.
- The conduct check is the first step: no clutch verb, including `clutch view status`, runs before it.

## Boundary contract
### Operator prompt wording
- disposition: extend
- owner: clutch/specs/ask/plan-ticket-drain.md and clutch/specs/ask/plan-ticket-serve.md
- consumers: `clutch prompt plan-ticket-drain`, `clutch prompt plan-ticket-serve`, and the operator models that follow them
- observable change: the first `Before you start` bullet and the first `Delegation` bullet of both specs carry the covered/uncovered sort and the first-step rule
- compatibility: the phrases `read the host's agent conduct files`, `conduct files`, `explicit override` and `the engine authored`, the order `conduct files` before `clutch host doctor` before `clutch provider probe` before `clutch prompt drain-loop`, and every other line of both specs stay as they are
- acceptance: criteria 1-4
- tests: tests/integration/test_ask_plan_conduct_covered.py
- post-merge source of truth: the two spec files

## Scope in / Scope out
Scope in, identically in both specs:
- Replace the first `Before you start` bullet. It keeps its opening sentence "Before any other step or engine starts, read the host's agent conduct files (the files its agents load as standing instructions)." and adds: run no clutch verb before this step is done; a rule that forbids only an action this prompt or `clutch prompt drain-loop` delegates (the Recommendation verdicts, the ticket edits a Recommendation names, the roadmap rows in Closing each phase) is covered, and running this prompt is the owner's explicit override of it, so list it in one line and do not ask; quote every other rule that forbids an action the delegation needs once, in one message that ends with the question, and run nothing until the owner answers; with no uncovered rule, say so and continue without waiting.
- Replace the first `Delegation` bullet's last sentence: a host conduct rule that forbids the ticket edits a Recommendation names is covered, not a conflict.

Scope out: `drain-loop.md` and every other prompt; `CORE_TEMPLATE`; the owner decision that an uncovered conflict stops the run; any new verb or flag.

Simpler approach rejected: delete the conflict check, since this repo's rules are all covered. Other hosts' conduct files carry rules the delegation does not settle, which is why `plan-drain-conduct-conflicts` added the check.

## Scope fence
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/plan-ticket-serve.md
- tests/integration/test_ask_plan_conduct_covered.py

## Acceptance criteria
1. In both rendered prompts the text `run no clutch verb` precedes the first `clutch view status`; checked by `tests/integration/test_ask_plan_conduct_covered.py`. A prompt that lets status run first fails it.
2. Both rendered prompts contain `covered` and `running this prompt is the owner's explicit override`, and `one message that ends with the question`; checked by `tests/integration/test_ask_plan_conduct_covered.py`.
3. Both prompts still contain `read the host's agent conduct files` and `explicit override`, and in each `conduct files` precedes `clutch host doctor`, which precedes `clutch provider probe`; checked by `tests/integration/test_ask_plan_drain.py` and `tests/integration/test_ask_plan_serve.py`, unchanged.
4. `tests/unit/test_ask_plan_drain.py` and `tests/unit/test_main_help.py` still pass unchanged.

## Verification
```
./dev.py test tests/integration/test_ask_plan_conduct_covered.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_serve.py tests/unit/test_ask_plan_drain.py tests/unit/test_main_help.py
```

## Definition of rejected
- A prompt in which an uncovered conflict no longer stops the run.
- Either prompt still tells the operator to wait for an override of an action it delegates in the same text.
- Wording that names a provider, a machine path or a verb that does not exist.
- A change to any file outside the fence.

## Time budget
- expected: 15m
- stuck: 30m
