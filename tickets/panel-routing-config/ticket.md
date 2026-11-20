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
- clutch/config.py::_check_references
- clutch/providers.py::_route
- clutch/providers.py::resolve
- clutch/providers.py::candidates
- clutch/providers.py::judge_independence_finding
- clutch/doctor.py
- clutch/docs/host-contract.md#Complete field inventory
- docs/stage-panels-plan.md#Target design
- tests/unit/test_route_kinds_filter.py
- tests/unit/test_route_kinds_judge.py

## Goal / Why
Roadmap row 66 (stage panels plan, ticket 2). Today a routing row cannot ask for several independent calls, so no stage can run as a panel. After this ticket a routing row may carry an optional `panel: {size, combine}`, config load refuses a row whose combiner does not fit its surface, a new provider function returns the members a panel call would use, and `clutch host doctor` reports a panel row whose members can only run one at a time. Nothing fans out yet: the driver, the combiners' use and the `panel_facts` signal belong to `review-panel` (roadmap row 67), which calls the new function. A host that sets no `panel` sees no change.

Rules, all from the panels plan section 1 and decisions 19:
- `size` is an integer 1 to 3; `combine` is one of `findings-union`, `majority-verdict`, `best-of-n`. Both keys are required inside `panel`.
- Surface fit, refused at config load with `ConfigError` keyed `routing.<i>.panel.combine`: `best-of-n` only on `implement`; `findings-union` only on `review` and `requisition_review`; `majority-verdict` only on `diagnose`, `triage` and `review_visual`.
- Member assignment, `providers.panel_members(config, tier, surface, kind=None)`: it returns `size` `Served` entries. When the row has at least `size` candidates, member `k` is candidate `k` in row order; otherwise every member is the first candidate (independent samples of one model). A row without `panel` returns one entry, the same as `resolve`.
- A row serves a surface other than its own only through the `review` fallback in `_route`; a fallback row's `panel` was declared for `review`, so `panel_members` returns a single entry (size 1) when the served row's surface is not the requested surface, never the review combiner on `diagnose`.
- Doctor: a `panel` row, emitted only when a finding exists, fails when a panel row of size above 1 resolves every member to providers whose `limits.concurrency` is 1 (members then run in turn, so the panel's wall time is multiplied). Like the `judge` row, it makes doctor print FAIL and exit 2; it names the routing row and the fix (raise `limits.concurrency` or add a second candidate on another provider).

## Boundary contract
### Routing config schema
- disposition: extend
- owner: clutch/config.py::Route
- consumers: load_config, snapshot_config, clutch/providers.py routing, the host contract field inventory
- observable change: a `routing` row accepts an optional `panel` with `size` 1 to 3 and `combine` from the closed set; absent means today's single call; an out-of-range size, an unknown combiner, an extra key, or a combiner on a surface it does not fit is a config load refusal
- compatibility: `schema_version` stays 1; every existing config loads unchanged because the key is optional; an older clutch refuses a config carrying `panel` as an unknown key, as "Version migration" in `clutch/docs/host-contract.md` already describes
- acceptance: criteria 1, 2 and 6
- tests: tests/unit/test_route_panel_config.py, tests/integration/test_host_contract.py
- post-merge source of truth: clutch/config.py::Route and the `config-fields` block in clutch/docs/host-contract.md

### Panel member assignment
- disposition: extend
- owner: clutch/providers.py (next to `resolve` and `candidates`)
- consumers: `review-panel` (roadmap row 67, the driver fan-out) and `clutch/doctor.py`
- observable change: new function `panel_members` returning the served members; `resolve` and `candidates` are unchanged
- compatibility: no existing caller changes; a row without `panel` yields the one entry `resolve` returns
- acceptance: criteria 3, 4 and 5
- tests: tests/unit/test_route_panel_config.py
- post-merge source of truth: clutch/providers.py::panel_members

### Doctor panel check
- disposition: extend
- owner: clutch/doctor.py::check
- consumers: `clutch host doctor`
- observable change: one extra `panel` row, present only when the finding exists; no row and no output change otherwise
- compatibility: a config without `panel` or with every panel member on a provider of concurrency above 1 prints exactly today's rows
- acceptance: criterion 7
- tests: tests/unit/test_route_panel_config.py
- post-merge source of truth: clutch/doctor.py

## Scope in / Scope out
Scope in: add `Panel` (a `StrictModel`) and `Route.panel` to `clutch/config.py`, with the closed combiner set and the surface-fit table owned there and checked in `_check_references` beside the implement-surface refusal; add `panel_members` and `panel_slots_finding(config)` to `clutch/providers.py`, the latter returning the finding text or `None` like `judge_independence_finding`; call it from `clutch/doctor.py` as a `panel` row after the `judge` row; update the `clutch/docs/host-contract.md` field inventory (a `Panel` entry, `Route` defaults gain `panel: unset`) and its prose after the `kinds` sentence; update the `host doctor` rows in `clutch/docs/host-running.md` and `docs/how-clutch-works.md` section 2, the `host doctor` command `does` text in `clutch/__main__.py`, and the `routing` paragraph in `docs/how-clutch-works.md` section 6.3 (one sentence on `panel`, stating no stage fans out yet). Create `tests/unit/test_route_panel_config.py`, reusing the `config` helper from `tests/unit/test_route_kinds_filter.py` by import.

Scope out: `clutch/panel.py` and its combiners (`panel-combiners`); the driver fan-out, member effect keys, `panel_facts` and every stage's use of the combined result (`review-panel`); making `panel.py` check combiner names against this set (it is pure and may not import config; `review-panel` pins the two sets equal in its own test). `panel_members` has no caller outside doctor until `review-panel`; it is the owner the driver must use, so no second assignment rule is written there.

Merge order with confirmed unrun tickets: `panel-combiners` fences only `clutch/panel.py` and its own tests, so it does not interact. `training-export` fences `clutch/__main__.py`, `docs/how-clutch-works.md` and `clutch/docs/host-running.md` too; this ticket edits only the `host doctor` row or `does` text and the routing paragraph there, and `training-export` edits the `training` group, so either order merges without a changed assertion.

## Scope fence
- clutch/config.py
- clutch/providers.py
- clutch/doctor.py
- clutch/__main__.py
- clutch/docs/host-contract.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/unit/test_route_panel_config.py

## Acceptance criteria
1. A routing row `panel: {size: 2, combine: findings-union}` on surface `review` loads with `Route.panel.size == 2` and `Route.panel.combine == "findings-union"`; a row without `panel` loads with `panel is None`; `size: 0`, `size: 4`, `combine: union`, an extra key inside `panel`, and a `panel` missing `combine` each raise `ConfigError`, not load: `./dev.py test tests/unit/test_route_panel_config.py`.
2. Surface fit: `findings-union` loads on `review` and `requisition_review` and raises `ConfigError` on `diagnose` (error key `routing.<i>.panel.combine`); `majority-verdict` loads on `diagnose`, `triage`, `review_visual` and raises on `review`; `best-of-n` loads on `implement` and raises on `review`: `./dev.py test tests/unit/test_route_panel_config.py`.
3. `panel_members` over a `review` row with candidates `[codex, claude]` and `panel: {size: 2, combine: findings-union}` returns `[codex, claude]` in that order, not `[codex, codex]`: `./dev.py test tests/unit/test_route_panel_config.py`.
4. Over a one-candidate row with `size: 3`, `panel_members` returns three entries all equal to the first candidate, not one entry and not an error; over a two-candidate row with `size: 3` it also returns the first candidate three times, not `[a, b, a]`: `./dev.py test tests/unit/test_route_panel_config.py`.
5. `panel_members(config, tier, "review")` for a row without `panel` returns exactly `[resolve(config, tier, "review")]`; `panel_members(config, tier, "diagnose")` with no `diagnose` row falling back to a `review` row that carries `findings-union` size 2 returns one entry, not two; a `kinds`-restricted panel row is chosen by the same kind rule as `resolve`: `./dev.py test tests/unit/test_route_panel_config.py`.
6. `host-contract.md` lists `Panel` with required `size` and `combine`, and `Route` defaults include `panel: unset`: `./dev.py test tests/integration/test_host_contract.py`.
7. `doctor.check` returns a failing `panel` row naming the routing row when a `size: 2` panel row's candidates are all providers with `limits.concurrency: 1`, returns no `panel` row when one member's provider has `concurrency: 2`, and returns no `panel` row for a `size: 1` panel or a row without `panel`: `./dev.py test tests/unit/test_route_panel_config.py`.
8. The closed-set and host-contract scans still pass with the new model and constants: `./dev.py test tests/integration/test_closed_sets_single_owner.py tests/integration/test_closed_sets_remaining.py tests/integration/test_vocabularies.py tests/integration/test_host_contract.py tests/unit/test_main_help.py tests/unit/test_host_running.py`.

## Verification
```
./dev.py test tests/unit/test_route_panel_config.py tests/unit/test_route_kinds_filter.py tests/unit/test_route_kinds_judge.py
./dev.py test tests/integration/test_host_contract.py tests/integration/test_doctor.py
./dev.py test tests/integration/test_closed_sets_single_owner.py tests/integration/test_closed_sets_remaining.py tests/integration/test_vocabularies.py
./dev.py test tests/unit/test_main_help.py tests/unit/test_host_running.py
```

## Definition of rejected
- A stage, driver, or journal change that fans out calls, or any use of `panel` outside config load, `panel_members` and doctor.
- A second member-assignment rule outside `providers.panel_members`, or a combiner-name set defined outside `clutch/config.py`.
- A panel row whose `diagnose` fallback applies the review combiner.
- A config without `panel` that loads differently or prints a new doctor row.

## Time budget
- expected: 25m
- stuck: 50m
