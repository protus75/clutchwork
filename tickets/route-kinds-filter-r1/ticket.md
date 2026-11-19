---
state: draft
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/config.py::Route
- clutch/providers.py::resolve
- clutch/providers.py::candidates
- clutch/providers.py::routed_conduct_paths
- clutch/providers.py::ProviderLLM.call
- clutch/llm.py::LLMRequest
- clutch/driver.py::Driver.run
- clutch/doctor.py
- clutch/__main__.py::stuck_ceiling_finding
- clutch/__main__.py::_lint
- clutch/tickets.py::KINDS
- clutch/docs/host-contract.md#Complete field inventory
- docs/gemini-graphics-refactor-plan.md#B3. Routing by ticket kind (`route-kinds-filter`)
- tests/integration/test_lint_verb.py
- tests/integration/test_doctor.py

## On-demand
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- clutch/stages.py
- tests/integration/test_host_contract.py

## Goal / Why
Roadmap row 51 (Gemini plan B3). Today a routing row maps only `(tier, surface)` to candidates, so every ticket kind is served by the same model. After this ticket:

1. A routing row may carry an optional `kinds:` list. `resolve()` and `candidates()` take the ticket's kind and pick, in order: a `(tier, surface)` row whose `kinds` names the kind; a `(tier, surface)` row with no `kinds`; then the `(tier, review)` fallback with the same two steps. A row with `kinds` never serves a kind it does not name, and never serves a call with no ticket kind. The ticket-bound Implement, Review and Diagnose calls pass the ticket's kind.
2. `clutch host doctor` reports a failing `judge` row, and `clutch ticket lint` reports a finding on a `graphics` ticket, when the `review_visual` route resolves to the same provider and the same model as the graphics `implement` route. The judge must not be the model that produced the candidate (plan B3, judge independence). Detection is exactly same provider and same model; the plan's "or an image model for the judge" clause is not built, because deciding that a model is an image model needs a model-name list this ticket does not invent.

This lets a host route graphics tickets to an image model while every other kind keeps its model, and it is the routing that `visual-review-surface` (row 53) builds on.

## Boundary contract
### Routing config schema
- disposition: extend
- owner: clutch/config.py::Route
- consumers: load_config, snapshot_config, clutch/providers.py routing, the host contract field inventory
- observable change: a `routing` row accepts an optional `kinds` list of ticket kinds; absent means every kind; an empty list or a value not in `clutch.tickets.KINDS` is a config load refusal
- compatibility: `schema_version` stays 1; every existing config loads unchanged because the key is optional; an older clutch refuses a config carrying `kinds` as an unknown key, as "Version migration" in `clutch/docs/host-contract.md` already describes
- acceptance: criteria 1 and 7
- tests: tests/unit/test_route_kinds_filter.py, tests/integration/test_host_contract.py
- post-merge source of truth: clutch/config.py::Route and the `config-fields` block in clutch/docs/host-contract.md

### Route resolution
- disposition: extend
- owner: clutch/providers.py::resolve and clutch/providers.py::candidates
- consumers: ProviderLLM.call, ProviderLLM.admitted_call, routed_conduct_paths, caps, policy, baseline
- observable change: both take an optional `kind` (default None) and choose the row in the order the Goal states; with kind None, rows carrying `kinds` are skipped; one private row selector serves both functions
- compatibility: with no `kinds` row in the config every call resolves exactly as today; the missing-row refusal keeps its `ProviderSetupError` and road
- acceptance: criteria 2, 3, 4 and 5
- tests: tests/unit/test_route_kinds_filter.py
- post-merge source of truth: clutch/providers.py

### LLM request and driver call
- disposition: extend
- owner: clutch/llm.py::LLMRequest and clutch/driver.py::Driver.run
- consumers: clutch/providers.py::ProviderLLM, clutch/stages.py
- observable change: `LLMRequest` gains `kind: str | None = None`; `Driver.run` gains keyword `kind` copied onto every `LLMRequest` it builds; `ProviderLLM.call` and `admitted_call` resolve with `req.kind`; `stages.implement`, `stages.review` and `stages.diagnose` pass `kind=ticket.frontmatter.kind`
- compatibility: every other `Driver.run` caller and `LLMRequest` construction omits it and keeps today's routing
- acceptance: criterion 6
- tests: tests/unit/test_route_kinds_filter.py
- post-merge source of truth: clutch/llm.py, clutch/driver.py

### Judge independence check
- disposition: create
- owner: clutch/providers.py (one pure function `judge_independence_finding(config)`)
- consumers: clutch/doctor.py (`judge` row) and clutch/__main__.py::_lint (graphics tickets)
- observable change: for each tier that has a routing row whose `kinds` names `graphics`, the function resolves `implement` with kind `graphics` and `review_visual` with kind `graphics` (a missing `review_visual` row falls back to `review`, as `resolve` does) and returns a message naming both when provider name and model are equal; otherwise None. A tier whose resolution raises `ProviderSetupError` (unset placeholder, no row) is skipped, because other doctor rows already report that. Doctor adds a failing `judge` row only on a finding, like the `parallel` row; lint prints the finding for a `graphics` ticket and exits 1.
- compatibility: a config with no `kinds: [graphics]` row, and every non-graphics ticket, produces no new output
- acceptance: criteria 8 and 9
- tests: tests/unit/test_route_kinds_judge.py, tests/integration/test_route_kinds_judge_lint.py
- post-merge source of truth: clutch/providers.py::judge_independence_finding
- closest existing: `doctor.check`'s `parallel` row and `__main__.stuck_ceiling_finding`; each is specific to its own fact and cannot hold a routing comparison
- earning reason: two production consumers (doctor and lint) need the same comparison; a single owner prevents two copies of the rule

## Scope in / Scope out
Scope in:
- `clutch/config.py`: `Route` gains `kinds: Annotated[list[str], Field(min_length=1)] | None = None` with a field validator refusing a value not in `clutch.tickets.KINDS`, naming the accepted kinds. Import `KINDS` inside the validator, not at module top (`clutch.tickets` imports `clutch.gates`, which imports `clutch.config`). Do not copy the kind names.
- `clutch/providers.py`: one private row selector used by `resolve` and `candidates`, replacing their two copies of the lookup and review fallback; `resolve(config, tier, surface, kind=None)`, `candidates(config, tier, surface, kind=None)`; `ProviderLLM.call` and `admitted_call` pass `req.kind`; `routed_conduct_paths` passes each route's first `kinds` entry (or None) so a provider served only on a `kinds` row still gets its conduct file; new `judge_independence_finding`.
- `clutch/llm.py`: `LLMRequest.kind: str | None = None`.
- `clutch/driver.py`: `Driver.run` and its inner runner gain keyword `kind`, set on the `LLMRequest`.
- `clutch/stages.py`: the `ctx.driver.run` calls in `diagnose`, `implement` and `review` pass `kind=ticket.frontmatter.kind`. Nothing else changes there.
- `clutch/doctor.py`: the `judge` row, added after the `parallel` row.
- `clutch/__main__.py`: `_lint` prints the finding for a `graphics` ticket and counts it as a finding; update the `clutch host doctor` and `clutch ticket lint` help text to state the new check. No other change.
- `clutch/docs/host-contract.md`: in the `config-fields` block set the `Route` defaults to include `{kinds: unset}`, and add one sentence after the block stating what `kinds` does and the resolution order.
- `clutch/docs/host-running.md`: update only the `host doctor` and `ticket lint` verb rows to mention the judge-independence check.
- `docs/how-clutch-works.md`: update only the section describing routing (8.2) and the verb table row text for doctor and lint if it describes them.
- New tests: `tests/unit/test_route_kinds_filter.py`, `tests/unit/test_route_kinds_judge.py`, `tests/integration/test_route_kinds_judge_lint.py` (follows the harness of `tests/integration/test_lint_verb.py`; tmp repo only). The unit file runs the new `_lint` lines through `clutch.__main__._lint` with a fake checkout: a `tmp_path` repo holding `tickets/<stem>/ticket.md` and the collision config, fake git methods returning `git_common_dir`, an empty `status_porcelain` and empty `_run` output for the evidence listing, and the journal under `tmp_path`. The integration file keeps the real-git CLI check.
- `tests/integration/test_host_contract.py`: only the edit its inventory comparison forces for the new `Route` field.

Scope out:
- Provider drought admission checks and `caps.next_rung` resolve with no kind and are not changed by this ticket.
- Ticket-bound calls outside `stages.py` (`acceptance.py`, `rework.py`, `mergequeue.py`) and ticketless surfaces pass no kind and are served by rows without `kinds`.
- The `review_visual` surface spec, the image-model detection clause, this repo's `config.yaml`, and any overlap check between routing rows (first matching row in file order serves, as today).

## Scope fence
- clutch/config.py
- clutch/providers.py
- clutch/llm.py
- clutch/driver.py
- clutch/stages.py
- clutch/doctor.py
- clutch/__main__.py
- clutch/docs/host-contract.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/integration/test_host_contract.py
- tests/unit/test_route_kinds_filter.py
- tests/unit/test_route_kinds_judge.py
- tests/integration/test_route_kinds_judge_lint.py

## Acceptance criteria
1. A config whose routing row carries `kinds: [bug]` loads with `Route.kinds == ["bug"]`; `kinds: []` and `kinds: [epic]` each raise `ConfigError`, not load; a row without `kinds` loads with `kinds is None`; checked by `./dev.py test tests/unit/test_route_kinds_filter.py`.
2. With medium rows `implement kinds:[bug] -> a`, `implement -> b`, `review kinds:[bug] -> c`, `review -> d`: `resolve(cfg, "medium", "implement", "bug").model == "a"`, kind `feature` gives `b`, no kind gives `b` (not `a`), and `resolve(cfg, "medium", "diagnose", "bug").model == "c"` while kind `feature` gives `d`; checked by `./dev.py test tests/unit/test_route_kinds_filter.py`.
3. With medium rows `implement kinds:[bug] -> a` and `review -> d` only, `resolve(cfg, "medium", "implement", "feature").model == "d"`, not `a`; with `implement kinds:[bug]` and `review kinds:[bug]` as the only medium rows, the same call raises `ProviderSetupError`, not a served model; checked by `./dev.py test tests/unit/test_route_kinds_filter.py`.
4. `candidates(cfg, "medium", "implement", "bug")` returns every candidate of the `kinds:[bug]` row in configured order, and kind `feature` returns the no-`kinds` row's candidates, not the bug row's; checked by `./dev.py test tests/unit/test_route_kinds_filter.py`.
5. When the only route served by a `claude` provider is a `kinds:[bug]` implement row and every other row is served by `codex`, `routed_conduct_paths` returns both `AGENTS.md` and `CLAUDE.md`, not `AGENTS.md` alone; checked by `./dev.py test tests/unit/test_route_kinds_filter.py`.
6. With fakes, `Driver.run(..., kind="bug")` hands the LLM a request with `kind == "bug"` and a call without `kind` hands `kind is None`; `ProviderLLM.call` with `LLMRequest(kind="bug")` invokes the adapter of the `kinds:[bug]` row's provider and with `kind=None` the plain row's provider; and a fake driver records `kind` equal to the ticket's frontmatter kind for `stages.implement`, `stages.review` and `stages.diagnose`; checked by `./dev.py test tests/unit/test_route_kinds_filter.py`.
7. The `config-fields` inventory matches `config.Route` with `kinds` as an unset default; checked by `./dev.py test tests/integration/test_host_contract.py`.
8. `judge_independence_finding` returns a message naming the provider and model when the `kinds:[graphics]` implement row and the `review_visual` row (or, absent that row, the `review` row) serve the same provider and model, and returns None, not a message, when the models differ, when no row names `graphics`, or when resolution raises `ProviderSetupError` for the placeholder model; `doctor.check` on that config returns a failing `judge` row and on a differing-model config returns no `judge` row; and a named test in the same file runs `clutch.__main__._lint` against a `tmp_path` repo with fake git methods and a journal under `tmp_path`, where a `graphics` ticket under the collision config prints the finding and returns 1, not 0, and a `feature` ticket under the same config returns 0; checked by `./dev.py test tests/unit/test_route_kinds_judge.py`.
9. `clutch ticket lint` on a valid `graphics` ticket in a repo whose config has the same-model collision prints the finding and exits 1, exits 0 with the models differing, and exits 0 for a `feature` ticket under the collision config; checked by `./dev.py test tests/integration/test_route_kinds_judge_lint.py`.
10. Every existing test passes, including `tests/integration/test_providers.py`, `tests/integration/test_doctor.py`, `tests/integration/test_lint_verb.py`, `tests/integration/test_ladder.py` and `tests/unit/test_main_help.py`; checked by `./dev.py test`.

## Verification
```
./dev.py test tests/unit/test_route_kinds_filter.py tests/unit/test_route_kinds_judge.py tests/integration/test_route_kinds_judge_lint.py tests/integration/test_host_contract.py
./dev.py test
```

## Definition of rejected
A row with `kinds` serves a kind it does not name or a call with no kind; kind names are copied out of `clutch.tickets`; `resolve` and `candidates` keep separate row-selection code; `schema_version` changes; routing changes for any config with no `kinds` row; the judge check fires on a config with no graphics row or on a non-graphics ticket; the judge check guesses image models by name.

## Time budget
- expected: 30m
- stuck: 60m
