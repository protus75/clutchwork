---
state: confirmed
source: box:roadmap_row
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/driver.py::Driver.from_config
- clutch/runner.py::bind
- clutch/runner.py::Checkout

## On-demand
- clutch/__main__.py
- clutch/triage.py
- eval/harness.py
- eval/diagnose.py

## Goal / Why
`Driver.from_config` takes the caller's `Journal` as a required keyword `journal` and no longer builds its own `Journal(config.state_dir, clock)`. Today every checkout-bound caller builds a Driver, then overwrites it with `driver.journal = checkout.journal; driver.effects = Effects(checkout.journal)`. That builds a journal nobody uses and scans the journal twice per bind (roadmap row 99, finishing row 20). After this change the Driver's `journal` is the object passed in, and `driver.effects` is the one `Driver.__init__` already builds from it, so the two overwrite lines go away at all five sites.

## Scope in / Scope out
In:
- `Driver.from_config` gains a required keyword-only `journal: Journal` and passes it to the constructor in place of `Journal(config.state_dir, clock)`.
- Delete the two overwrite lines (`driver.journal = ...`, `driver.effects = Effects(...)`) in `clutch/runner.py` (`bind` and the second binder near line 531), `clutch/triage.py` (two sites) and `clutch/__main__.py` (two sites). Each caller passes `journal=checkout.journal`. Drop an `Effects` import only if it becomes unused there.
- `eval/harness.py`, `eval/diagnose.py` and the tests that call `Driver.from_config` pass `journal=Journal(config.state_dir, clock)`, the expression `from_config` used to run itself. This changes no assertion.
- `tests/unit/test_roadmap_accept.py`: its fake `from_config` (near line 318) returns a bare `SimpleNamespace()` that gets `journal` and `effects` only from the overwrite lines in `clutch/__main__.py`. Change the fake to build the driver from the passed journal, e.g. `return SimpleNamespace(journal=kw['journal'], effects=Effects(kw['journal']))`. Add the import that needs. The assertions near lines 323 and 334 stay unchanged.
- `tests/integration/test_stages.py` and `tests/integration/test_daemon_composition.py` wrap `Driver.from_config` and forward `*args, **kwargs`; they change only if a call they make lacks `journal`.
- A new `tests/integration/test_driver_overwrite_source.py` reads the source of `clutch/runner.py`, `clutch/triage.py` and `clutch/__main__.py` from the repo and fails if either overwrite assignment is present.

Out:
- `Checkout` and `StageContext` carrying `log` and `box` (the other half of row 99). Each Box construction differs (`clutch/daemon.py` wires `arrival`/`recover`, `clutch/roadmap.py` has two forms), so that is a separate ticket. Do not touch those constructors or `EngineLog` builds.
- Any change to `Checkout` fields or its positional call sites in tests.
- `docs/roadmap.md` (the engine strikes rows).

## Scope fence
- clutch/driver.py
- clutch/runner.py
- clutch/triage.py
- clutch/__main__.py
- eval/harness.py
- eval/diagnose.py
- tests/unit/test_driver_from_config_journal.py
- tests/unit/test_roadmap_accept.py
- tests/unit/test_evidence_envelope.py
- tests/integration/test_driver_overwrite_source.py
- tests/integration/test_diagnose_eval.py
- tests/integration/test_providers.py
- tests/integration/test_driver.py
- tests/integration/test_merge.py
- tests/integration/test_echo_stage.py
- tests/integration/test_eval_harness.py
- tests/integration/test_stages.py
- tests/integration/test_requisition.py
- tests/integration/test_mergequeue.py
- tests/integration/test_llm_effect.py
- tests/integration/test_daemon_composition.py
- tests/regress_requisition_stage_events.py
- tests/regress_requisition_events_owner_stem.py

## Acceptance criteria
1. A new unit test builds `Driver.from_config(config, llm=..., env={}, clock=..., sleep=..., journal=j)` under `tmp_path` and asserts `driver.journal is j`, not a fresh `Journal`; run by `./dev.py test tests/unit/test_driver_from_config_journal.py`.
2. The same unit test asserts that calling `Driver.from_config` without `journal` raises `TypeError`, not a silently built journal; run by `./dev.py test tests/unit/test_driver_from_config_journal.py`.
3. The integration test scans the source text of `clutch/runner.py`, `clutch/triage.py` and `clutch/__main__.py` and fails if `driver.journal = ` or `driver.effects = ` is present in any of them; run by `./dev.py test tests/integration/test_driver_overwrite_source.py`.
4. `./dev.py test` passes in full, with no assertion in an edited existing test changed.

## Verification
```
./dev.py test
```

## Definition of rejected
The branch keeps a default or fallback that builds a journal inside `from_config`, leaves any `driver.journal =` or `driver.effects =` overwrite in `clutch/`, edits `Checkout`, `StageContext`, `Box` or `EngineLog` wiring, or changes a test assertion to make it pass.

## Time budget
- expected: 30m
- stuck: 60m
