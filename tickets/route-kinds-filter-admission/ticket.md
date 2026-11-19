---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
- route-kinds-filter

## Context
- clutch/providers.py::ProviderSession.drought
- clutch/caps.py::next_rung
- clutch/caps.py::capability
- clutch/serve.py::Serve.select
- clutch/__main__.py::build_daemon_core
- clutch/drain.py::_Drain._select
- tests/unit/test_premise_overruled.py
- tests/integration/test_drain_eligible_callers.py
- docs/gemini-graphics-refactor-plan.md#B3. Routing by ticket kind (`route-kinds-filter`)

## On-demand
- clutch/runner.py
- docs/how-clutch-works.md

## Goal / Why
Part two of roadmap row 51 (Gemini plan B3). After `route-kinds-filter`, a ticket's Implement, Review and Diagnose calls are served by the routing row that names the ticket's kind, but the checks that decide whether and where that ticket runs still resolve with no kind: the provider drought check before dispatch (`ProviderSession.drought`) and the Implement rung ladder (`caps.next_rung`). For a host that routes one kind to its own provider, a ticket of that kind is then admitted while its own provider is down and fails mid-run, or is parked because an unrelated provider is down; and an escalation compares the models of rows that will never serve it, so it can skip a rung or climb to a tier whose Implement model for that kind is the same. After this ticket, `drought` and `next_rung` take the ticket's kind, and every caller that holds the ticket passes `ticket.frontmatter.kind`, so admission and escalation look at the same row the call will use.

## Boundary contract
### Drought check and rung ladder
- disposition: extend
- owner: clutch/providers.py::ProviderSession.drought and clutch/caps.py::next_rung
- consumers: clutch/runner.py (`run_ticket` Implement admission, the Diagnose drought check in `drive`, the escalation in `failure_terminal`), clutch/serve.py::Serve.select, clutch/__main__.py::build_daemon_core dispatch, clutch/drain.py::_Drain._select
- observable change: `drought(config, tier, surface, kind=None)` checks the candidates `providers.candidates` returns for that kind; `next_rung(config, tier, effort, kind=None)` compares Implement models resolved for that kind; each caller listed passes `kind=ticket.frontmatter.kind` as a keyword
- compatibility: for a config with no `kinds` row every result is identical to today; the journaled `provider_drought` record keeps its `{tier, surface, providers}` shape, and `provider_holds` in `build_daemon_core`, which re-checks a parked record with no ticket in hand, keeps calling with no kind
- acceptance: criteria 1 to 5
- tests: tests/unit/test_route_kinds_admission.py
- post-merge source of truth: clutch/providers.py, clutch/caps.py

## Scope in / Scope out
Scope in:
- `clutch/providers.py`: `ProviderSession.drought` gains the keyword `kind=None` and passes it to `candidates`.
- `clutch/caps.py`: `next_rung` gains the keyword `kind=None` and passes it to `resolve`.
- `clutch/runner.py`: the `next_rung` call and the two `drought` calls (Diagnose in `drive`, Implement in `run_ticket`) pass `kind=ticket.frontmatter.kind`.
- `clutch/serve.py`: the `drought` call in `Serve.select` passes `kind=ticket.frontmatter.kind`.
- `clutch/__main__.py`: the `drought` call in `build_daemon_core`'s `dispatch` passes `kind=ticket.frontmatter.kind`. `provider_holds` is unchanged.
- `clutch/drain.py`: the `drought` call in `_Drain._select` passes `kind=t.frontmatter.kind`.
- `tests/unit/test_premise_overruled.py`: only the `next_rung` monkeypatch lambda changes, to accept the `kind` keyword.
- `tests/integration/test_drain_eligible_callers.py`: only the `drought` fake lambda changes, to accept the `kind` keyword.
- `docs/how-clutch-works.md`: in section 6 (the rung paragraph that begins "`escalate`, an Implement `premise_failed`") say the next Implement model is the one resolved for the ticket's kind, and in section 8.3 say the drought check uses the ticket's kind. Nothing else.
- New `tests/unit/test_route_kinds_admission.py`: configs under `tmp_path` and fakes only.

Scope out:
- The `provider_drought` record shape and the `ProviderDrought` raised inside `ProviderLLM.admitted_call`; `provider_holds` re-checks with no kind, and a stem it releases early is re-checked with its kind at dispatch and parked again.
- The routing schema and `resolve`/`candidates` (`route-kinds-filter`), and the judge check (`route-kinds-filter-judge`).
- `clutch/doctor.py`, `clutch/acceptance.py`, `clutch/rework.py`, `clutch/mergequeue.py`.

## Scope fence
- clutch/providers.py
- clutch/caps.py
- clutch/runner.py
- clutch/serve.py
- clutch/__main__.py
- clutch/drain.py
- docs/how-clutch-works.md
- tests/unit/test_premise_overruled.py
- tests/integration/test_drain_eligible_callers.py
- tests/unit/test_route_kinds_admission.py

## Acceptance criteria
1. With medium rows `implement kinds:[bug] -> provider A` and `implement -> provider B`, and A unavailable to the session, `session.drought(cfg, "medium", "implement", kind="bug")` returns a drought naming A, and `kind="feature"` returns `None`, not a drought; checked by `./dev.py test tests/unit/test_route_kinds_admission.py`.
2. With `implement kinds:[bug]` rows serving one model at `medium`, `high` and `max`, and plain `implement` rows serving a different model at each of those tiers, `next_rung(cfg, "medium", "medium", kind="bug")` returns `{"tier": "medium", "effort": "high"}` (an effort step), not `{"tier": "high", ...}`, while `next_rung(cfg, "medium", "medium")` returns `{"tier": "high", "effort": "medium"}`; checked by `./dev.py test tests/unit/test_route_kinds_admission.py`.
3. With fakes, `run_ticket` for a `kind: bug` ticket calls `drought` with `kind="bug"` for `implement`, and `Serve.select`, `build_daemon_core`'s dispatch and `_Drain._select` each pass the ticket's kind, not `None`; checked by `./dev.py test tests/unit/test_route_kinds_admission.py`.
4. The escalation in `runner.failure_terminal` calls `next_rung` with `kind` equal to the ticket's kind; checked by `./dev.py test tests/unit/test_route_kinds_admission.py tests/unit/test_premise_overruled.py`.
5. A parked `provider_drought` record still has exactly the keys `tier`, `surface` and `providers`; checked by `./dev.py test tests/integration/test_provider_cooldown_failover.py`.
6. Every existing test passes, including `tests/integration/test_ladder.py`, `tests/integration/test_drain_eligible_callers.py` and `tests/integration/test_daemon_composition.py`; checked by `./dev.py test`.

## Verification
```
./dev.py test tests/unit/test_route_kinds_admission.py tests/unit/test_premise_overruled.py tests/integration/test_drain_eligible_callers.py
./dev.py test
```

## Definition of rejected
A caller holding a ticket checks drought or rung with no kind; the `provider_drought` record shape changes; routing selection is copied out of `providers.candidates`/`resolve`; behavior changes for a config with no `kinds` row.

## Time budget
- expected: 25m
- stuck: 50m
