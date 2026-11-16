---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- none

## Context
- clutch/caps.py
- clutch/config.py::Caps
- clutch/observe.py::capability
- clutch/audit.py::audit
- clutch/drain.py::record_reoffer
- tests/unit/test_premise_overruled.py
- tests/integration/test_closed_sets.py::test_caps_closed_sets_and_constants
- tests/integration/test_config.py::test_valid_config_loads_from_cwd_with_shipped_defaults
- docs/how-clutch-works.md#6.4 Caps and escalation
- docs/roadmap-driver-plan.md#2. The supervisor step

## Goal / Why
Roadmap row 89 (`docs/roadmap.md`, owning design `docs/roadmap-driver-plan.md` section 2) adds a supervisor that keeps a Reject-queue ticket after a reviewed Rework edit, as the owner did by hand 78 times. The plan's departure table and step 3 set its accounting:

- A supervisor keep starts a new lineage, as an operator keep does, so the edited ticket gets a fresh cap budget and its authored capability rung.
- `caps.supervise`, default 2 (open decision 1, Proposed option), bounds supervisor keeps per operator lineage. Each keep draws one `cap_consumed` unit, so a supervisor keep never resets its own bound.

Today none of that accounting exists. `clutch/caps.py::lineage` starts after the last `reject_verdict keep` with `actor: operator` only, so a keep by any other actor leaves every spent cap spent. That is right for the drain's `actor: machine` re-offer keeps and wrong for a supervisor keep. `clutch/config.py::Caps` has no `supervise` field. `caps.consume` refuses any cap outside `DECLARED_CAPS`, so a `supervise` draw cannot be journaled, and `clutch/audit.py::audit` would flag one as `declared_cap`. `clutch/observe.py::capability`, which `watch` uses to show a stem's effective tier, folds the same operator-only window.

This ticket lands that accounting, the cap half of row 89. After it, a `reject_verdict keep` with `actor: supervisor` starts a lineage for every count and for capability, in the engine and in `watch`. A machine keep still resets nothing. `caps.supervise` exists with default 2. `supervise` draws are declared and audited. `caps.supervise_draws` counts them since the last operator keep only. `supervisor-rework` journals the keeps and draws and checks the bound; nothing journals `actor: supervisor` before it merges.

## Scope in / Scope out
Scope in:
- `clutch/config.py::Caps`: a last field `supervise: Count = 2`.
- `clutch/caps.py`:
  - `DECLARED_CAPS` becomes `CAPS + ("hardening", "supervise")`, and its comment says `supervise` counts supervisor keeps and never routes. `CAPS` does not change, so `spent` and `remaining` never name `supervise` and a spent `supervise` cap never routes a stem.
  - `lineage` gains a keyword `actors: tuple[str, ...] = ("operator", "supervisor")` and starts after the last `reject_verdict keep` whose `actor` is in `actors`. Every existing caller keeps the default, so `draws`, `remaining`, `failed_attempts`, `spent` and `capability` all restart at a supervisor keep.
  - A new function `supervise_draws(events, stem) -> int` counts the stem's `cap_consumed` events with `cap: supervise` in `lineage(events, stem, actors=("operator",))`.
- `clutch/observe.py::capability`: its keep window restarts at a `reject_verdict keep` whose actor is `operator` or `supervisor`, matching `caps.capability`. Nothing else in `clutch/observe.py` changes.
- Existing tests, each changed in that one assertion only:
  - `tests/integration/test_config.py::test_valid_config_loads_from_cwd_with_shipped_defaults`: the `cfg.caps.model_dump()` dict gains `"supervise": 2`.
  - `tests/integration/test_closed_sets.py::test_caps_closed_sets_and_constants`: the `DECLARED_CAPS` tuple gains `"supervise"` last. The `CAPS` and `LEVELS` assertions do not change.
- `clutch/docs/host-contract.md`, the `config-fields` block: both `caps` default maps (the `Config` row and the `Caps` row) gain `supervise: 2` last. `tests/integration/test_host_contract.py` checks them against the model and is not edited.
- `docs/how-clutch-works.md` section 6.4. The lineage sentence becomes "every event since the last operator keep or supervisor keep (`reject_verdict keep actor: supervisor`)". "only an operator `confirm` does" becomes "only an operator `confirm` or a supervisor keep does". The cap table gains the row `` `supervise` | 2 | each supervisor keep; counted since the last operator keep, so supervisor keeps never reset it and it never routes a stem ``. No other section changes.
- New tests in two new files: `tests/unit/test_supervise_cap_lineage.py` for the pure `caps`, `Caps` and `audit` behavior, run against in-memory `Event` lists as `tests/unit/test_premise_overruled.py` builds them (`clutch/caps.py` and `clutch/config.py` have positive unit floors in `test-gate.toml`); and `tests/integration/test_supervise_cap_lineage.py` for `observe.capability`, which reads a ticket file.

Scope out:
- Anything that journals `actor: supervisor` or a `supervise` draw, the Reject-queue trigger, Rework, and `rework.md`. Those are `supervisor-rework` and `rework-supervise-gate`.
- `clutch/drain.py` (`parked_blob`, `awaiting_operator`, `reofferable`, `record_reoffer`), `clutch/runner.py` (`verdict_locked`'s operator-only repeat-keep check), `clutch/status.py`, and `clutch/stats.py`, which already counts keeps by actor. None of them changes.
- The `attempts`, `diagnosis`, `retry`, `infra`, `premise_bounce`, `quarantine` and `poison` defaults; this repo's `config.yaml`; and `clutch/specs/ask/drain-loop.md`.

## Scope fence
- clutch/config.py
- clutch/caps.py
- clutch/observe.py
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- tests/integration/test_config.py
- tests/integration/test_closed_sets.py
- tests/unit/test_supervise_cap_lineage.py
- tests/integration/test_supervise_cap_lineage.py

## Acceptance criteria
1. `tests/unit/test_supervise_cap_lineage.py::test_supervisor_keep_starts_a_lineage` builds stem `work`'s events: `running`, a `gate_failed` terminal at `check`, then three `cap_consumed` `retry` draws. It asserts `spent(Caps(), events, "work") == "retry"`. With a `reject_verdict keep actor: supervisor` appended, it asserts `lineage(events, "work")` is exactly the events after that keep, `failed_attempts(events, "work") == 0`, and `spent(Caps(), events, "work") is None`. With `actor: machine` in place of `supervisor`, `spent` is still `"retry"`. Ruled out: a supervisor keep that leaves the cap spent (today's behavior), and a machine keep that resets it.
2. `tests/unit/test_supervise_cap_lineage.py::test_supervisor_keep_resets_capability` uses a `SimpleNamespace` ticket `work` authored `medium`/`medium`. After a `retry` draw carrying `rung: {"tier": "high", "effort": "max"}`, `capability(ticket, events) == ("high", "max")`. After a following supervisor keep it is `("medium", "medium")`. Ruled out: the escalated rung surviving a supervisor keep.
3. `tests/unit/test_supervise_cap_lineage.py::test_supervise_draws_count_since_the_operator_keep` builds a `supervise` draw, a supervisor keep, a second `supervise` draw, and a second supervisor keep, and asserts `supervise_draws(events, "work") == 2` and `draws(events, "work", "supervise") == 0`. A following machine keep leaves the count at 2. A following operator keep makes it 0. Ruled out: a supervisor keep resetting its own bound (count 0 or 1 after the second keep), and a machine keep resetting it.
4. `tests/unit/test_supervise_cap_lineage.py::test_supervise_cap_is_declared_and_never_routes` asserts four things. `Caps().supervise == 2`. `Caps(supervise=0)` raises `pydantic.ValidationError`. `"supervise" in DECLARED_CAPS` and `"supervise" not in CAPS`. With `Caps(supervise=1)`, events holding two `supervise` draws and nothing else for `work` give `spent(..., "work") is None`. It also asserts that `consume` on an in-memory journal appends one `cap_consumed` body `{"cap": "supervise", "ticket_sha": "sha"}`, and that `audit([(event,)])` of that event returns no `declared_cap` violation. Ruled out: a `supervise` draw refused by `consume` or flagged by the audit (today's behavior), and a spent `supervise` cap that routes a stem.
5. `tests/integration/test_supervise_cap_lineage.py::test_watch_capability_restarts_at_a_supervisor_keep` writes `tmp_path/tickets/work/ticket.md` with frontmatter `agent_tier: medium` and `agent_effort: medium`. It calls `observe.capability(SimpleNamespace(root=tmp_path), events, "work", "implement")` over dict events holding a `retry` `cap_consumed` with rung `high`/`max`. The result is `"high/max (escalated)"`, and with a later supervisor keep appended it is `"medium/medium"`. Ruled out: `watch` showing an escalated tier the engine no longer uses.
6. `./dev.py test tests/integration/test_config.py tests/integration/test_closed_sets.py tests/integration/test_host_contract.py` exits 0 with only the two assertions `## Scope in / Scope out` names changed.
7. `./dev.py test tests/integration/test_caps.py tests/integration/test_reject_queue.py tests/integration/test_ladder.py tests/integration/test_drain.py tests/unit/test_premise_overruled.py tests/unit/test_caps_requisition_park.py tests/unit/test_drain_reoffer.py tests/integration/test_audit.py` exits 0 unedited: operator and machine keeps behave as before.
8. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_supervise_cap_lineage.py
./dev.py test tests/integration/test_supervise_cap_lineage.py
./dev.py test tests/integration/test_config.py tests/integration/test_closed_sets.py tests/integration/test_host_contract.py
./dev.py test tests/integration/test_caps.py tests/integration/test_reject_queue.py tests/integration/test_ladder.py tests/integration/test_drain.py tests/unit/test_premise_overruled.py tests/unit/test_caps_requisition_park.py tests/unit/test_drain_reoffer.py tests/integration/test_audit.py
./dev.py test
```

## Definition of rejected
The branch is rejected if `supervise` joins `CAPS` or can route a stem; if a machine keep resets any count; if anything journals `actor: supervisor` or a `supervise` draw outside a test; if `clutch/drain.py`, `clutch/runner.py`, `clutch/status.py` or `clutch/stats.py` changes; if a cap default other than the new `supervise: 2` changes; if `caps.lineage` and `observe.capability` disagree on where a lineage starts; or if any existing assertion other than the two named in `## Scope in / Scope out` is changed or weakened.

## Time budget
- expected: 45m
- stuck: 120m
