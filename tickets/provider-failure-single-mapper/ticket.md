---
state: confirmed
source: human
priority: P2
kind: chore
---

## Depends on
- none

## Context
- chupa/stages.py::run_stages
- chupa/driver.py::Driver._run
- chupa/driver.py::Driver.provider_failure
- chupa/runner.py::drive
- chupa/requisition.py::review_ticket
- docs/roadmap.md#2.1
- tests/integration/test_stages.py::CONFIG
- tests/integration/test_stages.py::repo
- tests/integration/test_stages.py::run
- tests/integration/test_stages.py::agent

## Goal / Why
`run_stages` in `chupa/stages.py` ends its per-stage `try` with an `except Exception as exc` block that maps `ProviderDrought` to a `ProviderDroughtResult` and `ProviderCallError` to `provider_failure(...)` plus an `infra_error` result. It is a copy of the mapping in `chupa/runner.py::drive`, and the copy hard-codes `surface="requisition_review"` for failures in Implement, Check, and Review.

The copy cannot run. Every stage operation calls the model through `Driver._run`, whose `failed` closure already maps both exceptions, with the stage's own surface, before anything returns to `run_stages`. A reproduction on 2026-11-14 at `328d07d9` confirmed it: a scripted implementer raising `ProviderCallError` with `failure_class="quota_exhausted"` during Implement produced one Suggestion Box `failure_report` with `stage="implement"`, and `run_stages` returned an `infra_error` implement result without reaching its own `except`. The mapper in `runner.drive` is live, because `review_ticket` calls the model outside `Driver._run`.

Two copies of one mapping, one of them wrong and unreachable, is the accretion `docs/roadmap.md` §2.1 row 8 names. When this ticket is done, `run_stages` has no provider-exception mapping: an exception a stage operation raises propagates, as every non-provider exception already does, and two tests pin that a provider failure in Implement still reaches the Box labelled `implement` and ends the run with `infra_error`.

## Scope in / Scope out
- In: `chupa/stages.py::run_stages`. Delete the `except Exception as exc:` block: its local imports of `ProviderDroughtResult`, `ProviderCallError`, and `ProviderDrought`, the two `isinstance` branches, and the `else: raise`. The `try` keeps its `CancelledError` handling and the `finally` that clears `boundary.active`; the `with ctx.driver.stage(...)` context and the `if stage == "check": event.end(...)` line are unchanged. No other statement in `run_stages` changes, and nothing else in `chupa/stages.py` changes.
- In: `tests/unit/test_run_stages_propagates.py` (new). Builds a `StageContext` from in-memory stand-ins (a driver whose `journal.read()` returns `[]` and whose `provider_failure` is an `AsyncMock`, a git whose `rev_parse` returns a fixed sha), patches `chupa.stages.ticket_change_findings` to return `[]` and `chupa.stages.implement` to raise `ProviderCallError`, and asserts `run_stages` raises that error and never calls `provider_failure`. No disk, process, or network.
- In: `tests/integration/test_provider_failure_surface.py` (new). Uses the `repo` fixture and the `run` helper from `tests/integration/test_stages.py` with a script whose implement item raises `ProviderCallError("codex", "quota exhausted", rc=1, stderr_tail="usage limit reached", failure_class="quota_exhausted", paved_road="wait for provider 'codex' to recover from quota_exhausted, then retry")`. Asserts the implement result is `infra_error` with a `quota_exhausted` finding, `check` is absent from the results, and the Box holds exactly one `failure_report` with `stage == "implement"` and `outcome == "infra_error"`.
- Out: `chupa/runner.py::drive`'s mapper and `Driver._run`'s `failed` closure, which stay as they are. `chupa/requisition.py`. Any change to what a provider failure produces.

## Scope fence
- chupa/stages.py
- tests/unit/test_run_stages_propagates.py
- tests/integration/test_provider_failure_surface.py

## Acceptance criteria
1. `tests/unit/test_run_stages_propagates.py` asserts `pytest.raises(ProviderCallError)` around `run_stages` with `implement` patched to raise it, and that the driver's `provider_failure` was not awaited. The wrong result it rules out is a returned `StagesRun` whose implement result is `infra_error`, which the deleted block produced. The test runs under `chupa.testguard` without disk, process, or network.
2. `tests/integration/test_provider_failure_surface.py` asserts implement outcome `infra_error`, finding code `quota_exhausted`, no `check` key in `run.results`, and one Box `failure_report` with `stage == "implement"` and `outcome == "infra_error"`. The wrong result it rules out is `stage == "requisition_review"`.
3. `grep -n provider_failure chupa/stages.py` prints nothing, and `grep -n "ProviderDroughtResult" chupa/stages.py` prints nothing.
4. `./dev.py test` exits 0, with `chupa/stages.py` at or above its `test-gate.toml` floor of 12.

## Verification
```
./dev.py test
```

## Definition of rejected
- A provider-exception mapping remains anywhere other than `chupa/runner.py::drive` and `chupa/driver.py::Driver._run`.
- `runner.drive`'s mapper, `Driver._run`'s `failed` closure, or `Driver.provider_failure` changes.
- The observed result of a provider failure in any stage changes: the `infra_error` result, or the Box report's `stage`.

## Time budget
- expected: 20m
- stuck: 45m
