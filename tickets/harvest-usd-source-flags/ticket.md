---
state: draft
source: box:suggestion
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/artifacts.py::Harvest
- clutch/artifacts.py::Cost
- clutch/runner.py::harvest
- clutch/runner.py::harvest_orphan
- clutch/providers.py::CliAdapter.within_budget
- tests/integration/test_harvest.py
- tests/unit/test_harvest_redaction.py
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py

## On-demand
- clutch/specs/diagnose.md

## Goal / Why
A failed attempt's `harvest.json` says whether `usd` was reported by the provider or is the flat `limits.est_cost_per_call_usd`, whether the provider can enforce a budget cap, and which provider and model ran the attempt. The Diagnose spec forbids a budget-stop lesson unless the record shows a reported cost.

Today `Harvest.usd` is a bare sum of `Cost.usd`. For a provider whose stream reports no cost, `providers.py` fills `usd` with the flat estimate (`config.yaml` sets 1.00 for the codex route that runs Implement), so every failed codex attempt shows `usd: 1.0`. Diagnose read that as a per-attempt spend cap in `tickets/conflict-discard-rerun/diagnosis.json`, and the lesson shaped the retry and split advice. The same lesson named the wrong provider for attempt 0, because the record carries no provider or model.

## Boundary contract
### Harvest artifact
- disposition: extend
- owner: clutch/artifacts.py
- consumers: clutch/runner.py (`harvest`, `harvest_orphan`), the Diagnose stage prompt that embeds harvest records, existing `tickets/*/attempts/*/harvest.json` files
- observable change: `Harvest` gains optional fields `provider: str | None`, `model: str | None`, `usd_estimated: bool | None` and `budget_capable: bool | None`, all defaulting to `None`. `harvest` fills them from the last LLM `Cost` entry of the run's results and the provider's config; the provider and adapter lookup runs only when `results` holds an LLM `Cost`, so a run with `results=()` and a provider-less config (as in `tests/unit/test_harvest_redaction.py`) leaves all four `None` and keeps passing. `harvest_orphan` leaves them `None` because it has no results. `usd_estimated` is true when the provider's adapter reports no cost; `budget_capable` is true only when the adapter reports cost, the only case where the adapter's `within_budget` accepts a budget cap without comparing it to the flat estimate.
- compatibility: existing harvest.json files stay valid because the new fields default to `None`; no other field changes
- acceptance: a harvest for a failed run on a non-cost-reporting provider has `usd_estimated: true`, `budget_capable: false`, and the provider and model names; a run on a cost-reporting provider has `usd_estimated: false`, `budget_capable: true`
- tests: new unit test for the model and for `runner.harvest`, new integration test for the harvest seam
- post-merge source of truth: clutch/artifacts.py

### Diagnose spec
- disposition: extend
- owner: clutch/specs/diagnose.md
- consumers: the Diagnose stage
- observable change: one added rule: a lesson never names a spend cap, budget stop or per-attempt cost limit unless the record shows `usd_estimated: false` and the findings or reason name a budget stop; it names provider and model only as the record states them
- compatibility: reply format unchanged; version bumped to the next minor above the version on main
- acceptance: the spec text carries the rule and the version pins match
- tests: `tests/unit/test_specs.py` and `tests/integration/test_specs_delimiter_note.py` pins
- post-merge source of truth: clutch/specs/diagnose.md

## Scope in / Scope out
Scope in: the four optional `Harvest` fields; filling them in `harvest` (provider and model from the last LLM `Cost`, source flags from the provider config and adapter `reports_cost`); one rule in `clutch/specs/diagnose.md` with the minor version bump; updating the diagnose version pin in `tests/unit/test_specs.py` and `tests/integration/test_specs_delimiter_note.py` (only that expectation changes in each); two new test files. Scope out: removing or changing cost accounting, `Cost`, `LLMResult` or `providers.py`; lesson length and ordering; rewriting existing harvest.json files.

## Scope fence
- clutch/artifacts.py
- clutch/runner.py
- clutch/specs/diagnose.md
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py
- tests/unit/test_artifacts_harvest_cost_source.py
- tests/integration/test_harvest_cost_source.py

## Acceptance criteria
1. `Harvest.model_validate` of a record without the new keys succeeds and yields `None` for each of the four fields, not an error (`./dev.py test tests/unit/test_artifacts_harvest_cost_source.py`).
2. `tests/unit/test_artifacts_harvest_cost_source.py` calls `runner.harvest` with a fake ctx (a `SimpleNamespace` with fs, git and driver fakes and `lift_outbox` monkeypatched, as `tests/unit/test_harvest_redaction.py` does) and `results` holding a `StageResult` whose `Cost` names `codex` and a model: the written harvest.json has `usd_estimated` true, `budget_capable` false, and that provider and model, not `None` (`./dev.py test tests/unit/test_artifacts_harvest_cost_source.py`).
3. The same unit test with a `Cost` naming `claude` asserts `usd_estimated` false and `budget_capable` true, not the reverse (`./dev.py test tests/unit/test_artifacts_harvest_cost_source.py`).
4. The `harvest` seam for a failed run whose `Cost` names a provider with no reported cost and a 1.00 estimate writes `usd_estimated: true`, `budget_capable: false`, the provider and the model; `usd_estimated` is not `null` or `false` (`./dev.py test tests/integration/test_harvest_cost_source.py`).
5. The same seam for a cost-reporting provider writes `usd_estimated: false` and `budget_capable: true`, not `true` for estimated (`./dev.py test tests/integration/test_harvest_cost_source.py`).
6. `harvest_orphan` writes `None` for all four fields, not a guessed provider (`./dev.py test tests/integration/test_harvest_cost_source.py`).
7. `clutch/specs/diagnose.md` carries the budget-stop rule and a version one minor above the previous one, and both version pins match it (`./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py`).

## Verification
```
./dev.py test tests/unit/test_artifacts_harvest_cost_source.py tests/integration/test_harvest_cost_source.py tests/integration/test_harvest.py tests/integration/test_harvest_orphans.py tests/unit/test_harvest_redaction.py tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py
```

## Definition of rejected
The branch changes how `usd` is computed or removes cost accounting, makes the new fields required so old harvest.json files fail to load, or edits the diagnose spec without the version bump and pins.

## Time budget
- expected: 20m
- stuck: 40m
