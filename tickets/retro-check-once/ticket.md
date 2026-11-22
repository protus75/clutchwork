---
state: confirmed
source: human
priority: P0
kind: bug
---

## Depends on
- none

## Runs before
- retro-due-one-owner

## Context
- clutch/serve.py::Serve.check_retro
- clutch/serve.py::Serve.merge
- clutch/retro.py::measurements
- clutch/retro.py::select_trigger
- clutch/retro.py::production_evidence
- clutch/drain.py::_Drain._run_retro
- tests/unit/test_phase_events.py
- tests/unit/test_drain_retro_once_per_settle.py
- tests/regress_phase_step_kinds.py

## Goal / Why
Under `engine serve`, one merge writes two overlapping `retro_check` phases to the engine log. In the evidence, `phase_start` fires at 13:29:21.207 and again at 13:29:21.670, then both end. The doubling comes from two callers. The dispatch wrapper's `finally` (`clutch/serve.py` near line 178) calls `Serve.check_retro` when its ticket ends terminal. `Serve.merge` (near line 528) also calls it after delivering that same ticket's merge result. Nothing dedupes the second call. Each check also awaits `production_evidence`, which runs `git show` over every Check record in the retro window. That took 74 s at 13:29 and blocked the merge poll. No trigger in `select_trigger` reads those git-derived fields; `merged_count` and `spikes` both come from the journal-only `measurements(window)`.

When done:
- `Serve.check_retro` runs at most once per new terminal transition in the journal, so one merge gives one `retro_check` phase pair.
- The check decides "due" from `measurements(window)` with no `await` inside it, so two checks can never overlap.
- The VS Code Recent Steps view shows one retro check per settle, not two.

## Boundary contract
### Serve retro check
- disposition: extend
- owner: clutch/serve.py
- consumers: `Serve.dispatch` wrapper `finally`, `Serve.merge` poll, Recent Steps via the engine log
- observable change: `check_retro` returns without logging when the journal's count of terminal transitions equals the count recorded at its last successful check; the due decision uses `measurements(window)`, not `production_evidence`
- compatibility: `phase_start`/`phase_end` names, the `retro_check` phase, and the outcome vocabulary (`due`, `not_due`, `failed`) are unchanged; `check_retro` stays an `async def`, so call sites and `tests/integration/serve_rig.py` are untouched
- acceptance: a second call with no new terminal transition logs nothing; a failed check does not record the count, so the next call retries
- tests: tests/unit/test_serve_retro_check_once.py, tests/unit/test_phase_events.py
- post-merge source of truth: clutch/serve.py

## Scope in / Scope out
Scope in:
- In `clutch/serve.py`, add `self.retro_checked = None` in `Serve.__init__`, next to `retro_due`.
- `Serve.check_retro` first reads the journal once, before `phase_start`, and counts `STATE_TRANSITION` events whose `to` is in `TERMINAL_STATES`. When that count equals `self.retro_checked`, it returns before logging anything. If the journal read itself raises, the exception propagates with no phase events, because no check started. The `project_window` and trigger work that follow use the events from that same read.
- Otherwise run the check as now, but replace `await production_evidence(window, c)` with `measurements(window)`. Record `self.retro_checked = count` only after a successful check. Mirror `_Drain._run_retro`.
- The body of `check_retro` has no `await`, so a concurrent caller cannot interleave with it.
- Update the `clutch.retro` import in `clutch/serve.py`: drop `production_evidence` and add `measurements`.
- In `tests/unit/test_phase_events.py`, change `test_serve_retro_events` and `test_serve_retro_failure` in four ways:
  - Set `s.retro_checked = None`.
  - Make the fake journal `read` return `[SimpleNamespace(type=EventType.STATE_TRANSITION, body={"to": "merged"})]` instead of `["journal"]`.
  - Monkeypatch `serve.measurements` (returning `"evidence"`) instead of `serve.production_evidence`. The `evidence` failure case raises from `measurements` and still expects a `failed` pair.
  - The `journal` failure case now expects `RuntimeError("journal")` with an empty log, not a `failed` pair.
- Add `tests/unit/test_serve_retro_check_once.py`.
- Add the carried reproducer `tests/regress_serve_retro_check_once.py`. It follows `tests/regress_phase_step_kinds.py`: it puts the repo root on `sys.path` and prints only the `regression_result` JSON object to stdout. It exits 0 on `pass`, 1 on `defect`, and 2 on `error` with a traceback on stderr. Setup:
  - Build `s = object.__new__(serve.Serve)` and set `s.retro_checked = None` and `s.retro_due = False`. Base ignores `retro_checked`.
  - Set `s.log` to an object whose `event(name, **fields)` appends `name` to a list.
  - Set `config = SimpleNamespace(retro=object())`.
  - Define a local `@dataclass class Checkout` with fields `config`, `journal` and `clock`, as `tests/unit/test_phase_events.py` does, because `check_retro` calls `dataclasses.replace` on the checkout. Set `s.checkout = Checkout(config, SimpleNamespace(read=lambda: [SimpleNamespace(type=EventType.STATE_TRANSITION, body={"to": "merged"})]), lambda: "now")`. `tests/unit/test_serve_retro_check_once.py` builds its checkouts the same way.
  - Set `s.control = SimpleNamespace(load_config=lambda: config)`.
  - Replace `serve.snapshot_config` with identity, `serve.project_window` with identity, `serve.suppressing_failure` with `lambda w: None`, and `serve.select_trigger` with `lambda *a, **k: None`.
  - Where the `serve` module has the attribute, replace `serve.production_evidence` with `AsyncMock(return_value={})` and `serve.measurements` with `lambda w: {}`.

  It awaits `check_retro()` twice in one `asyncio.run` and counts `phase_start` names. One is `pass`, two is `defect`, and an exception is `error`.

Scope out:
- `Retro.__call__` in `clutch/retro.py` and the drain path still run `production_evidence` before selecting a trigger. Unifying the due decision across drain and serve is `retro-due-one-owner`.
- Hiding `not_due` checks in Recent Steps is not part of this ticket.
- No change to `tests/integration/serve_rig.py` or any other hot test file.

## Scope fence
- clutch/serve.py
- tests/unit/test_phase_events.py
- tests/unit/test_serve_retro_check_once.py
- tests/regress_serve_retro_check_once.py

## Acceptance criteria
1. Take a journal holding one `merged` transition. Two sequential `await s.check_retro()` calls log exactly one `phase_start`/`phase_end` pair for `retro_check`, not two (`tests/unit/test_serve_retro_check_once.py`).
2. On the same journal, `asyncio.gather(s.check_retro(), s.check_retro())` logs exactly one `phase_start`, not two (`tests/unit/test_serve_retro_check_once.py`).
3. Append a `gate_failed` transition after a check, then call again: the second call logs a second pair. Append a `running` transition instead: it logs nothing (`tests/unit/test_serve_retro_check_once.py`).
4. A check whose `measurements` raises logs `failed` and leaves `retro_checked` unrecorded. The next call with the same journal logs a fresh pair, not nothing (`tests/unit/test_serve_retro_check_once.py`).
5. `check_retro` never calls `production_evidence`. A test monkeypatches `clutch.retro.production_evidence` to raise, and the check still ends `not_due` (`tests/unit/test_serve_retro_check_once.py`).
6. `./dev.py test tests/unit/test_phase_events.py tests/unit/test_serve_retro_check_once.py` exits 0.

## Verification
```
./dev.py test tests/unit/test_phase_events.py tests/unit/test_serve_retro_check_once.py tests/unit/test_serve_dispatch_containment.py
```

## Definition of rejected
- `check_retro` still awaits anything between `phase_start` and `phase_end`.
- The fix removes one of the two call sites instead of deduping in `check_retro`; that is `retro-due-one-owner`'s job.
- Any edit to `tests/integration/serve_rig.py` or another hot test file.

## Time budget
- expected: 12m
- stuck: 24m

## Regression
```
uv run python tests/regress_serve_retro_check_once.py
```
- carries: tests/regress_serve_retro_check_once.py
