---
state: confirmed
source: box:roadmap_row
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/daemon.py::apply_rework
- clutch/rework.py::rework
- clutch/requisition.py::review_ticket
- clutch/driver.py::Driver._run
- clutch/llmeffect.py
- clutch/stages.py::lift_outbox
- docs/roadmap-driver-plan.md#Target design

## Goal / Why
Today every Effect key a Rework step mints is built from the stem and an integer: `ticket-plane/{stem}/{attempt}/rework` in `apply_rework`, `llm/{stem}/{run_seq}/{surface}/{attempt}/{call_seq}` through `llm_key` for the rework call (`Driver._run` takes `run_seq` from the journal) and for each requisition review (`review_ticket` takes the attempt as `run_seq`), the rework state tree `state_dir/rework/{stem}/{attempt}/{call_seq}`, and `ticket-plane/{stem}/{attempt}/{kind}` in `lift_outbox`. A supervisor step that runs outside a run and journals no terminal leaves `run_seq` unchanged, so a reused attempt number mints keys a later run also mints, and that run replays the step's cached results.

After this ticket `apply_rework`, `rework`, `review_ticket`, `Driver.run` and `lift_outbox` take an optional `key_scope`. With a scope, every key and state-tree path they mint holds `<scope>-<n>` where the integer attempt or run sequence was, so the keys are disjoint from every unscoped key and from any other scope's. With no scope, every key is byte-identical to today's. This lets roadmap row `supervise-idle-point` call the supervisor step outside a run without replaying or poisoning any run's results.

## Scope in / Scope out
Scope in:
- `clutch/llmeffect.py`: add `scoped_seq(scope: str | None, n: int) -> int | str`. It returns `n` unchanged for `None`, returns `f"{scope}-{n}"` otherwise, and raises `ValueError` for a scope not matching `[a-z][a-z0-9]*` (so a scoped segment can never equal an integer or contain `/`). Widen the `run_seq` type of `llm_key` and `llm_call` to `int | str`. Nothing else changes in this file.
- `clutch/driver.py`: `Driver.run` and `Driver._run` take `key_scope: str | None = None`. `_run` computes `key_seq = scoped_seq(key_scope, seq)` once and passes it to both the `call_key` `llm_key` call and `llm_call(..., run_seq=key_seq)`, so the Effect key and the logged call key agree. Events, spool paths, `begin_watch` and the journal `run_seq` keep the integer `seq`.
- `clutch/requisition.py`: `review_ticket` takes `key_scope: str | None = None` and passes `scoped_seq(key_scope, run_seq)` as `run_seq` to `llm_call`; the `attempt` segment stays an integer.
- `clutch/rework.py`: `rework` takes `key_scope: str | None = None`, passes it to `ctx.driver.run` and to every `review_ticket` call, builds the state-tree path and the `prefix` used for `review_seq` with `scoped_seq(key_scope, attempt)` in the attempt position, so a scoped step counts only its own reviews.
- `clutch/daemon.py`: `apply_rework` takes `key_scope: str | None = None`, passes it to `rework`, and builds the publish key as `ticket-plane/{stem}/{scoped_seq(key_scope, attempt)}/rework`.
- `clutch/stages.py`: `lift_outbox` takes `key_scope: str | None = None` and uses `scoped_seq(key_scope, attempt)` in its key. No existing caller passes a scope; leave every caller unchanged.
- New `tests/unit/test_key_scope.py` (fakes only, `tmp_path` only; no process or network).

Scope out: callers of `apply_rework` in `clutch/runner.py` and the merge route (they pass no scope), the idle-point hook, spool paths, the `supervisor_attempt` signal, the journal `run_seq`, and any docs (an optional internal parameter changes no documented behavior).

## Scope fence
- clutch/llmeffect.py
- clutch/driver.py
- clutch/requisition.py
- clutch/rework.py
- clutch/daemon.py
- clutch/stages.py
- tests/unit/test_key_scope.py

## Acceptance criteria
1. `scoped_seq(None, 3)` returns the int `3`, not the string `"3"`; `scoped_seq("sup", 3)` returns `"sup-3"`; `scoped_seq("a/b", 3)`, `scoped_seq("", 3)` and `scoped_seq("7", 3)` each raise `ValueError`; checked by `./dev.py test tests/unit/test_key_scope.py`.
2. `llm_key("s", scoped_seq(None, 2), "rework", 1, 1)` equals `llm_key("s", 2, "rework", 1, 1)`, and `llm_key("s", scoped_seq("sup", 2), "rework", 1, 1)` differs from it and from the key under scope `"other"`; checked by `./dev.py test tests/unit/test_key_scope.py`.
3. With a fake effects recorder and a fake rework result, `apply_rework(..., attempt=0)` records the key `ticket-plane/<stem>/0/rework` and `apply_rework(..., attempt=0, key_scope="sup")` records `ticket-plane/<stem>/sup-0/rework`, not the unscoped key; a second unscoped run after the scoped one is not served from the scoped result; checked by `./dev.py test tests/unit/test_key_scope.py`.
4. For a scoped `rework` call every `llm/` key recorded by the fake driver (rework call and requisition reviews) contains `sup-` in the run-sequence position and none equals a key recorded by the same call without a scope; the state-tree path used is `rework/<stem>/sup-<attempt>/<call_seq>`; checked by `./dev.py test tests/unit/test_key_scope.py`.
5. `review_seq` in a scoped step ignores journaled `llm/<stem>/<attempt>/requisition_review/...` keys from an unscoped run of the same attempt number, so its first review is call 1, not call N+1; checked by `./dev.py test tests/unit/test_key_scope.py`.
6. `lift_outbox(..., attempt=4, key_scope="sup")` records `ticket-plane/<stem>/sup-4/<kind>`, and without a scope records `ticket-plane/<stem>/4/<kind>` unchanged; checked by `./dev.py test tests/unit/test_key_scope.py`.
7. Every existing test still passes with no scope given, which pins that unscoped keys are unchanged; checked by `./dev.py test`.
8. A real `Driver.run(..., key_scope="sup")` driven by a fake LLM, a `tmp_path` journal and effects store, and a trivial echo `LlmStage` records the effect key `llm/<stem>/sup-<seq>/<surface>/<attempt>/1`; the same call without a scope records `llm/<stem>/<seq>/<surface>/<attempt>/1`, and the journal `run_seq` stays the integer `<seq>` in both; checked by `./dev.py test tests/unit/test_key_scope.py`.

## Verification
```
./dev.py test tests/unit/test_key_scope.py
./dev.py test
```

## Definition of rejected
Any unscoped key, state-tree path or journal field differs from today's; a scoped key can equal an unscoped key or another scope's key; the scope is read from config, a global, or the journal instead of the parameter; a second key-building path is added beside `scoped_seq`; or a caller outside the fence is changed to pass a scope.

## Time budget
- expected: 30m
- stuck: 60m
