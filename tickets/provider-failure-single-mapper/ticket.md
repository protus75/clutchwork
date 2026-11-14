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
- tests/integration/test_provider_cooldown_failover.py::test_mid_run_drought_is_harvested_without_spine_draws
- tests/integration/test_stages.py::CONFIG
- tests/integration/test_stages.py::repo
- tests/integration/test_stages.py::run
- tests/integration/test_stages.py::agent

## Goal / Why
`run_stages` in `chupa/stages.py` ends its per-stage `try` with an `except Exception as exc` block that maps `ProviderDrought` to a `ProviderDroughtResult` and `ProviderCallError` to `provider_failure(...)` plus an `infra_error` result. It is a copy of the mapping in `chupa/runner.py::drive`, and the copy hard-codes `surface="requisition_review"` for failures in Implement, Check, and Review.

No production caller reaches the copy. Every stage operation calls the model through `Driver._run`, whose `failed` closure already maps both exceptions, with the stage's own surface, before anything returns to `run_stages`. The one model call that bypasses `Driver._run` is `review_ticket`, and in `chupa/` it is called only from `runner.py`, `rework.py`, `author.py`, and `__main__.py` -- never from inside a stage operation. A reproduction on 2026-11-14 at `328d07d9` confirmed the block is not entered: a scripted implementer raising `ProviderCallError` with `failure_class="quota_exhausted"` during Implement produced one Suggestion Box `failure_report` with `stage="implement"`, and `run_stages` returned an `infra_error` implement result without reaching its own `except`. The mapper in `runner.drive` is live, because the `review_ticket` call it wraps is its own.

One test reaches the block, and only by manufacturing a caller production does not have: `test_mid_run_drought_is_harvested_without_spine_draws[True]` in `tests/integration/test_provider_cooldown_failover.py` monkeypatches `stages.review` with a stand-in that calls `review_ticket` from inside the Review stage, then asserts the `requisition_review` surface the block labels. A test-only caller does not make code live, so the `nested=True` parametrization goes with the block it pins.

A second copy of a mapping with no production caller is the accretion `docs/roadmap.md` §2.1 row 8 names. That row also names the wrong fix: `runner.drive`'s mapper wraps only the pre-stage `review_ticket` call it makes itself, not `run_stages`, so removing this block leaves no mapper over stage operations rather than "one mapper in `runner.py`". That is safe, because no production call inside a stage operation can raise either exception outside `Driver._run`, and the row must say so instead. When this ticket is done, `run_stages` has no provider-exception mapping: an exception a stage operation raises propagates, as every non-provider exception already does, and two tests pin that a provider failure in Implement still reaches the Box labelled `implement` and ends the run with `infra_error`.

## Scope in / Scope out
- In: `chupa/stages.py::run_stages`. Delete the `except Exception as exc:` block: its local imports of `ProviderDroughtResult`, `ProviderCallError`, and `ProviderDrought`, the two `isinstance` branches, and the `else: raise`. The `try` keeps its `CancelledError` handling and the `finally` that clears `boundary.active`; the `with ctx.driver.stage(...)` context and the `if stage == "check": event.end(...)` line are unchanged. No other statement in `run_stages` changes, and nothing else in `chupa/stages.py` changes.
- In: `tests/unit/test_run_stages_propagates.py` (new). Builds a `StageContext` from in-memory stand-ins (a driver whose `journal.read()` returns `[]` and whose `provider_failure` is an `AsyncMock`, a git whose `rev_parse` returns a fixed sha), patches `chupa.stages.ticket_change_findings` to return `[]` and `chupa.stages.implement` to raise `ProviderCallError`, and asserts `run_stages` raises that error and never calls `provider_failure`. No disk, process, or network.
- In: `tests/integration/test_provider_failure_surface.py` (new). Uses the `repo` fixture and the `run` helper from `tests/integration/test_stages.py` with a script whose implement item raises `ProviderCallError("codex", "quota exhausted", rc=1, stderr_tail="usage limit reached", failure_class="quota_exhausted", paved_road="wait for provider 'codex' to recover from quota_exhausted, then retry")`. Asserts the implement result is `infra_error` with a `quota_exhausted` finding, `check` is absent from the results, and the Box holds exactly one `failure_report` with `stage == "implement"` and `outcome == "infra_error"`.
- In: `tests/integration/test_provider_cooldown_failover.py`. Delete the `nested=True` half of `test_mid_run_drought_is_harvested_without_spine_draws`: drop the `@pytest.mark.parametrize("nested", [False, True])` decorator and the `nested` parameter, delete the `if nested:` branch in the local `review` stand-in together with its `FIRST_REVIEW`/`review_ticket`/`TICKET` imports, and reduce the surface assertion to `== "review"`. The `nested=False` behaviour, every other assertion in the test, and every other test in the file are unchanged.
- In: `docs/roadmap.md`. Correct §2.1 row 8 and the §3.1 defect-table row that repeat this ticket's old framing: the block has no production caller (only the deleted test case reached it), its `surface="requisition_review"` is the correct label for the only exception source that could reach it rather than a mislabel for Implement/Check/Review, and the outcome is that no mapper covers stage operations, not "one mapper in `runner.py`". Mark both rows done by this stem. No other row or section changes.
- Out: `chupa/runner.py::drive`'s mapper and `Driver._run`'s `failed` closure, which stay as they are. `chupa/requisition.py`. Any change to what a provider failure produces in production.

## Scope fence
- chupa/stages.py
- docs/roadmap.md
- tests/integration/test_provider_cooldown_failover.py
- tests/unit/test_run_stages_propagates.py
- tests/integration/test_provider_failure_surface.py

## Acceptance criteria
1. `tests/unit/test_run_stages_propagates.py` asserts `pytest.raises(ProviderCallError)` around `run_stages` with `implement` patched to raise it, and that the driver's `provider_failure` was not awaited. The wrong result it rules out is a returned `StagesRun` whose implement result is `infra_error`, which the deleted block produced. The test runs under `chupa.testguard` without disk, process, or network.
2. `tests/integration/test_provider_failure_surface.py` asserts implement outcome `infra_error`, finding code `quota_exhausted`, no `check` key in `run.results`, and one Box `failure_report` with `stage == "implement"` and `outcome == "infra_error"`. The wrong result it rules out is `stage == "requisition_review"`.
3. `grep -n provider_failure chupa/stages.py` prints nothing, and `grep -n "ProviderDroughtResult" chupa/stages.py` prints nothing.
4. `grep -n nested tests/integration/test_provider_cooldown_failover.py` prints nothing, and `./dev.py test tests/integration/test_provider_cooldown_failover.py` exits 0 collecting one `test_mid_run_drought_is_harvested_without_spine_draws` case, not two. The wrong result it rules out is the surviving `[True]` case erroring with an uncaught `ProviderDrought`.
5. `docs/roadmap.md` §2.1 row 8 and its §3.1 defect row no longer claim a hard-coded mislabel for Implement, Check, and Review, and no longer name "one mapper in `runner.py`" as the outcome.
6. `./dev.py test` exits 0, with `chupa/stages.py` at or above its `test-gate.toml` floor of 12.

## Verification
```
./dev.py test
```

## Definition of rejected
- A provider-exception mapping remains anywhere other than `chupa/runner.py::drive` and `chupa/driver.py::Driver._run`.
- `runner.drive`'s mapper, `Driver._run`'s `failed` closure, or `Driver.provider_failure` changes.
- The observed result of a provider failure raised by a production stage operation changes: the `infra_error` result, or the Box report's `stage`. The deleted `nested=True` case is not such a failure; it manufactured its own caller.
- `tests/integration/test_provider_cooldown_failover.py` loses or weakens any assertion other than the `nested=True` surface, or keeps the `nested=True` case by catching the propagated exception.

## Time budget
- expected: 20m
- stuck: 45m
