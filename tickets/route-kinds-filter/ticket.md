---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
none

## Context
- clutch/config.py::Route
- clutch/config.py::Candidate
- clutch/providers.py::resolve
- clutch/providers.py::candidates
- clutch/providers.py::routed_conduct_paths
- clutch/providers.py::ProviderLLM.admitted_call
- clutch/providers.py::ProviderLLM.call
- clutch/llm.py::LLMRequest
- clutch/driver.py::Driver.run
- clutch/stages.py::diagnose
- clutch/stages.py::implement
- clutch/stages.py::review
- clutch/docs/host-contract.md#Complete field inventory
- docs/gemini-graphics-refactor-plan.md#B3. Routing by ticket kind (`route-kinds-filter`)

## On-demand
- docs/how-clutch-works.md
- tests/integration/test_host_contract.py

## Goal / Why
Roadmap row 51 (Gemini plan B3, decided 2026-11-14: build it now). Today a routing row maps only `(tier, surface)` to candidates, so every ticket kind is served by the same model. After this ticket a routing row may carry an optional `kinds:` list, and the ticket-bound Implement, Review and Diagnose calls are served by the row that names the ticket's kind. `resolve()` and `candidates()` take a `kind` and pick, in order: a `(tier, surface)` row whose `kinds` names the kind; a `(tier, surface)` row with no `kinds`; then the `(tier, review)` fallback with the same two steps. A row with `kinds` never serves a kind it does not name, and never serves a call with no ticket kind. This lets a host route graphics tickets to an image model (the plan's example) without changing any other ticket's model, and it is the routing that `visual-review-surface` (row 53) and `panel-routing-config` (row 66) build on.

The ticket splits the row in three. This ticket is the schema and the resolver. `route-kinds-filter-admission` makes the provider drought check and the Implement rung ladder pass the ticket kind. `route-kinds-filter-judge` adds the judge-independence check to `host doctor` and ticket lint, and needs the `graphics` kind from `graphics-kind`.

## Boundary contract
### Routing config schema
- disposition: extend
- owner: clutch/config.py::Route
- consumers: load_config, snapshot_config, clutch/providers.py routing, the host contract field inventory
- observable change: a `routing` row accepts an optional `kinds` list of ticket kinds; absent means every kind; an empty list, or a value that is not in `clutch.tickets.KINDS`, is a config load refusal
- compatibility: `schema_version` stays 1; every existing config loads unchanged because the key is optional; an older clutch refuses a config carrying `kinds` as an unknown key, which "Version migration" in `clutch/docs/host-contract.md` already describes
- acceptance: criteria 1 and 7
- tests: tests/unit/test_route_kinds_filter.py, tests/integration/test_host_contract.py
- post-merge source of truth: clutch/config.py::Route and the `config-fields` block in clutch/docs/host-contract.md

### Route resolution
- disposition: extend
- owner: clutch/providers.py::resolve and clutch/providers.py::candidates
- consumers: ProviderLLM.call, ProviderLLM.admitted_call, routed_conduct_paths, ProviderSession.drought, caps.next_rung, policy, baseline, acceptance
- observable change: both take an optional `kind` (default None) and choose the row in the order the Goal states; with kind None, rows carrying `kinds` are skipped
- compatibility: with no `kinds` row in the config every call resolves exactly as today, so every existing caller and test is unchanged; the missing-row refusal keeps its `ProviderSetupError` and road
- acceptance: criteria 2, 3, 4 and 5
- tests: tests/unit/test_route_kinds_filter.py
- post-merge source of truth: clutch/providers.py

### LLM request and driver call
- disposition: extend
- owner: clutch/llm.py::LLMRequest and clutch/driver.py::Driver.run
- consumers: clutch/providers.py::ProviderLLM, clutch/stages.py
- observable change: `LLMRequest` gains `kind: str | None = None`; `Driver.run` gains a keyword `kind: str | None = None` that it copies onto every `LLMRequest` it builds; `ProviderLLM.call` and `ProviderLLM.admitted_call` resolve with `req.kind`; `stages.implement`, `stages.review` and `stages.diagnose` pass `kind=ticket.frontmatter.kind`
- compatibility: every other `Driver.run` caller and `LLMRequest` construction omits it and keeps today's routing
- acceptance: criteria 5 and 6
- tests: tests/unit/test_route_kinds_filter.py
- post-merge source of truth: clutch/llm.py, clutch/driver.py

## Scope in / Scope out
Scope in:
- `clutch/config.py`: `Route` gains `kinds: Annotated[list[str], Field(min_length=1)] | None = None`, with a field validator that refuses a value not in `clutch.tickets.KINDS` and names the accepted kinds in its message. Import `KINDS` inside the validator, not at module top: `clutch.tickets` imports `clutch.gates`, which imports `clutch.config`, so a top-level import is a cycle. `clutch.tickets.Kind` stays the one owner of the kind set (closed-sets-single-owner); do not copy the kind names.
- `clutch/providers.py`: one private row selector used by both `resolve` and `candidates`, replacing their two copies of the `next(...)` lookup and the review fallback. `resolve(config, tier, surface, kind=None)` and `candidates(config, tier, surface, kind=None)`. `ProviderLLM.call` and `ProviderLLM.admitted_call` pass `req.kind`. `routed_conduct_paths` passes, for each route, its first `kinds` entry (or None) so a provider served only on a `kinds` row still gets its conduct file.
- `clutch/llm.py`: `LLMRequest.kind: str | None = None`, after `budget_usd`.
- `clutch/driver.py`: `Driver.run` and `Driver._run` gain the keyword `kind: str | None = None`; `_run` sets it on the `LLMRequest` it builds.
- `clutch/stages.py`: the `ctx.driver.run` calls in `diagnose`, `implement` and `review` pass `kind=ticket.frontmatter.kind`. Nothing else changes in that file.
- `clutch/docs/host-contract.md`: in the `config-fields` block change the `Route` defaults to `{kinds: unset}`, and add one sentence to the prose after the block stating what `kinds` does and the resolution order. Nothing else in that file changes.
- `docs/how-clutch-works.md`: update only section 8.2 Routing to describe `kinds` and the resolution order.
- New `tests/unit/test_route_kinds_filter.py`: configs written under `tmp_path` and fakes only.

Scope out:
- The provider drought pre-dispatch check (`ProviderSession.drought` callers in `runner.py`, `serve.py`, `drain.py`, `__main__.py`) and `caps.next_rung`; they resolve with no kind until `route-kinds-filter-admission` merges.
- The judge-independence row in `host doctor` and the lint finding: `route-kinds-filter-judge`.
- Ticket-bound calls outside `stages.py` (`acceptance.py`, `rework.py`, `mergequeue.py`) and ticketless surfaces (author, triage, retro, requisition review, preflight) pass no kind and are served by rows without `kinds`.
- The `scheduler.parallel` doctor row in `clutch/doctor.py`, the `graphics` kind, the `review_visual` surface, and this repo's `config.yaml`.
- No duplicate-row or overlap check between rows; the first matching row in file order serves, as today.

## Scope fence
- clutch/config.py
- clutch/providers.py
- clutch/llm.py
- clutch/driver.py
- clutch/stages.py
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- tests/integration/test_host_contract.py
- tests/unit/test_route_kinds_filter.py

## Acceptance criteria
1. A config whose routing row carries `kinds: [bug]` loads, and the loaded `Route.kinds == ["bug"]`; `kinds: []` and `kinds: [epic]` each raise `ConfigError` instead of loading, and a row without `kinds` loads with `kinds is None`; checked by `./dev.py test tests/unit/test_route_kinds_filter.py`.
2. With medium rows `implement kinds:[bug] -> model a`, `implement -> model b`, `review kinds:[bug] -> model c`, `review -> model d`: `resolve(cfg, "medium", "implement", "bug").model == "a"`, `resolve(..., "implement", "feature").model == "b"`, `resolve(..., "implement").model == "b"` (not `a`), `resolve(..., "diagnose", "bug").model == "c"` and `resolve(..., "diagnose", "feature").model == "d"`; checked by `./dev.py test tests/unit/test_route_kinds_filter.py`.
3. With medium rows `implement kinds:[bug] -> a` and `review -> d` only, `resolve(cfg, "medium", "implement", "feature").model == "d"`, not `a`; and with `implement kinds:[bug]` and `review kinds:[bug]` as the only medium rows, `resolve(cfg, "medium", "implement", "feature")` raises `ProviderSetupError`, not a served model; checked by `./dev.py test tests/unit/test_route_kinds_filter.py`.
4. `candidates(cfg, "medium", "implement", "bug")` returns every candidate of the `kinds:[bug]` row in configured order, and `candidates(cfg, "medium", "implement", "feature")` returns the no-`kinds` row's candidates, not the bug row's; checked by `./dev.py test tests/unit/test_route_kinds_filter.py`.
5. When the only route served by a `claude` provider is a `kinds:[bug]` implement row and every other row is served by `codex`, `routed_conduct_paths` returns both `AGENTS.md` and `CLAUDE.md`, not `AGENTS.md` alone; checked by `./dev.py test tests/unit/test_route_kinds_filter.py`.
6. With fakes, `Driver.run(..., kind="bug")` hands the LLM an `LLMRequest` with `kind == "bug"` and a call without `kind` hands one with `kind is None`; `ProviderLLM.call` with an `LLMRequest(kind="bug")` invokes the adapter of the `kinds:[bug]` row's provider, and with `kind=None` the plain row's provider; and a fake driver records `kind` equal to the ticket's frontmatter kind for `stages.implement`, `stages.review` and `stages.diagnose`; checked by `./dev.py test tests/unit/test_route_kinds_filter.py`.
7. The `config-fields` inventory matches `config.Route` with `kinds` as an unset default; checked by `./dev.py test tests/integration/test_host_contract.py`.
8. Every existing test passes, including `tests/integration/test_providers.py`, `tests/integration/test_daemon_composition.py`, `tests/integration/test_ladder.py` and `tests/unit/test_closed_sets_single_owner.py`; checked by `./dev.py test`.

## Verification
```
./dev.py test tests/unit/test_route_kinds_filter.py tests/integration/test_host_contract.py
./dev.py test
```

## Definition of rejected
A row with `kinds` serves a kind it does not name or a call with no kind; the kind names are copied out of `clutch.tickets`; `resolve` and `candidates` keep separate row-selection code; `schema_version` changes; any existing caller's routing changes for a config with no `kinds` row; drought, rung, doctor or lint code changes.

## Time budget
- expected: 30m
- stuck: 60m
