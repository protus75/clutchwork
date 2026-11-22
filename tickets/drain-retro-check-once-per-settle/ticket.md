---
state: confirmed
source: human
priority: P2
kind: bug
---

## Depends on
- none

## Context
- clutch/drain.py::_Drain.__init__
- clutch/drain.py::_Drain._run
- clutch/drain.py::_Drain._run_retro
- clutch/serve.py::Serve.check_retro
- clutch/journal.py::TERMINAL_STATES
- clutch/retro.py::Retro
- tests/unit/test_phase_events.py
- tests/regress_phase_step_kinds.py

## Goal / Why
`engine drain` runs an unforced retro check at the top of every pass of its loop in `_Drain._run`, whenever it is between tickets. A pass that ends in `continue` without dispatching starts a new pass and a new check, even though no ticket settled. Examples: the journal changed during dispatch prep (`events != prepared_events`), or a driver task is pending. The evidence (`evidence/retro-evidence.txt`, from `.clutch/state/engine.log` on 2026-11-22) shows a drain handoff after the `check-owns-meta-headers` merge. The new process ran `preflight`, retro check 1 (`not_due`, 28 s), then the roadmap driver wrote a `roadmap_gate` signal, so the loop restarted and ran retro check 2 (`not_due`, 26 s) before dispatching `serve-flaky-tests-deterministic`. Nothing settled between the two checks, so check 2 could not change the outcome. It cost about 26 s of drain time and added a duplicate Recent Steps row.

`engine serve` already checks only after a ticket reaches a terminal state (`clutch/serve.py` calls `check_retro` when the last transition is in `TERMINAL_STATES`). After this ticket, the drain's unforced retro check follows the same rule. It runs on the first between-tickets point of each drain process, then again only when the journal's count of `state_transition` events whose `to` is in `TERMINAL_STATES` has grown since the last check that completed. A forced check (a new `retro_id` control request) always runs, as now.

## Boundary contract
### Drain retro check scheduling
- disposition: extend
- owner: clutch/drain.py
- consumers: the drain loop in `_Drain._run`, the `retro_check` phase events in `engine.log`, and the extension's Recent Steps rows that read them
- observable change: an unforced `_Drain._run_retro` call returns without calling the retro hook and without logging `phase_start`/`phase_end` for `retro_check` when the terminal-transition count equals the count recorded at the last completed check in this process
- compatibility: forced checks, the first unforced check in each process, and checks after a new terminal transition behave exactly as before; `Retro.__call__`, `select_trigger`, serve, and the phase event shape are unchanged
- acceptance: two unforced checks with no terminal transition between them call the hook once; a terminal transition between them makes the second run; a forced call always runs; a check that raises records nothing, so the next unforced call runs
- tests: tests/unit/test_drain_retro_once_per_settle.py and tests/regress_drain_retro_once_per_settle.py
- post-merge source of truth: clutch/drain.py

## Scope in / Scope out
Scope in:
- `clutch/drain.py`: in `_Drain.__init__`, add one field holding the terminal-transition count at the last completed unforced or forced check (`None` before the first). In `_Drain._run_retro`, when `forced` is false, count `state_transition` events in `self.c.journal.read()` whose `body["to"]` is in `TERMINAL_STATES` (already imported). If the count equals the stored count, return before logging or calling the hook. Store the count only after the hook returns without raising, for both forced and unforced calls. `_run` keeps its current call sites unchanged.
- `tests/unit/test_drain_retro_once_per_settle.py` (new): unit tests using fakes only (no repo files, processes, or network). They build `_Drain` through `__init__` with a `SimpleNamespace` checkout as described under Regression, and cover each Acceptance case.
- `tests/regress_drain_retro_once_per_settle.py` (new): a carried reproducer following `tests/regress_phase_step_kinds.py`. It builds `_Drain(checkout, None, frozenset())` through `__init__` with a `SimpleNamespace` checkout whose `config` has `state_dir`, `providers=[]`, `release.pypi_token=""` and `drain.max_runtime_hours=1`, plus `env={}`, a `clock` returning an aware `datetime`, `sleep=None`, `control=None`, and a `journal` whose `read()` returns one `state_transition` to `merged`. It replaces `clutch.drain.engine_log` with a no-op logger, sets `retro` to a fake hook with `due = False` and an async `abort_current`, and awaits `_run_retro(forced=False)` twice. Two hook calls print `defect` and exit 1, one call prints `pass` and exit 0, and any exception prints `error` and exits 2. At base this setup yields two calls (verified while authoring).
- `tests/unit/test_phase_events.py`: `test_drain_retro_events` builds `_Drain` with `object.__new__` and a checkout without a journal. Give that fake a `journal` whose `read()` returns `[]` and set the new field to `None`, so its existing expectations hold unchanged. Nothing else in that file changes.
- `docs/how-clutch-works.md` section 9.5: in the sentence "During a drain it runs between tickets, never between attempts of one ticket, when due…", add that a drain checks once when it starts, then only after a ticket settles or a retro is requested. Nothing else in the document changes.

Scope out:
- serve's retro check, `Retro.__call__`, `select_trigger`, retro thresholds, and the phase event vocabulary.
- The `continue` paths in `_Drain._run` and the roadmap driver: the extra loop pass stays, only its redundant retro check goes.
- Re-checking after a mid-process `config.yaml` retro settings change: like serve, the next check happens at the next settle.

## Scope fence
- clutch/drain.py
- tests/unit/test_drain_retro_once_per_settle.py
- tests/regress_drain_retro_once_per_settle.py
- tests/unit/test_phase_events.py
- docs/how-clutch-works.md

## Acceptance criteria
1. Two `_run_retro(forced=False)` calls with no new terminal transition between them call the retro hook once and log one `retro_check` start/end pair, not two (`tests/unit/test_drain_retro_once_per_settle.py`).
2. Appending a `state_transition` to a state in `TERMINAL_STATES` (for example `gate_failed`) between two unforced calls makes the second call run the hook, not skip it (`tests/unit/test_drain_retro_once_per_settle.py`).
3. A `state_transition` to a non-terminal state such as `running` between two unforced calls does not make the second call run (`tests/unit/test_drain_retro_once_per_settle.py`).
4. `_run_retro(forced=True)` runs the hook even when the count is unchanged since the last check (`tests/unit/test_drain_retro_once_per_settle.py`).
5. When the hook raises, `_run_retro` re-raises, logs `retro_check` `failed`, and the next unforced call with an unchanged count still runs the hook, not skips it (`tests/unit/test_drain_retro_once_per_settle.py`).
6. `uv run python tests/regress_drain_retro_once_per_settle.py` prints `{"regression_result": "pass"}` and exits 0 on the branch, and prints `defect` on the merge base.
7. The existing drain retro tests still pass unchanged: `./dev.py test tests/integration/test_drain.py -k retro` and `./dev.py test tests/unit/test_phase_events.py`.

## Verification
```
uv run python tests/regress_drain_retro_once_per_settle.py
./dev.py test tests/unit/test_drain_retro_once_per_settle.py tests/unit/test_phase_events.py
./dev.py test tests/integration/test_drain.py -k retro
./dev.py test
```

## Definition of rejected
Reject the branch if any of the following holds:
- a forced retro check can be skipped;
- the first unforced check in a drain process can be skipped;
- the gate keys on anything other than the journal's terminal-transition count (for example a timer, a loop counter, or `self.report`);
- serve, `clutch/retro.py`, or the phase event names or outcomes change;
- an existing assertion in `tests/integration/test_drain.py` is edited.

## Time budget
- expected: 20m
- stuck: 40m

## Regression
```
uv run python tests/regress_drain_retro_once_per_settle.py
```
- carries: tests/regress_drain_retro_once_per_settle.py
