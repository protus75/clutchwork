---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- retro-check-once

## Context
- clutch/serve.py::Serve.check_retro
- clutch/serve.py::Serve.merge
- clutch/serve.py::Serve.run
- clutch/serve.py::Serve.retro_pending
- clutch/retro.py::measurements
- clutch/retro.py::select_trigger
- clutch/retro.py::Retro.__call__
- clutch/drain.py::_Drain._run_retro
- tests/unit/test_phase_events.py
- tests/unit/test_retro_check_vocabulary.py

## On-demand
- tests/unit/test_stale_running.py
- tests/unit/test_paved_roads.py
- tests/unit/test_serve_dispatch_containment.py
- tests/unit/test_serve_retro_check_once.py
- tests/regress_serve_retro_check_once.py

## Goal / Why
`retro-check-once` stops the doubled, slow check, but the structure that produced it stays. Two things are wrong with that structure.

First, the retro due check is wired into the event sites. `Serve` calls `check_retro` in the dispatch wrapper's `finally` and again inside `Serve.merge`, under `async with self.core.admission.merging()`. Any work there holds the merge lock and the lane slot. At 13:29 on 2026-11-22 a 74 s check held up the merge queue. A third site added later would double-count again.

Second, "is a retro due" is decided in two places. `Serve.check_retro` builds the window and calls `select_trigger`. `Retro.__call__`, which the drain path runs on every settle, awaits `production_evidence` and its per-ticket `git show` before it calls `select_trigger`. So every drain-mode settle pays the git cost even when no retro is due.

When done:
- The serve maintenance loop in `Serve.run` is the only caller of `check_retro`. It runs next to the existing `retro_pending()` scheduling, never inside the merge lock or a dispatch `finally`.
- One pure function in `clutch/retro.py` maps a window and settings to a trigger. It reads `measurements(window)` and does no I/O. `Serve.check_retro` and `Retro.__call__` both call it. `Retro.__call__` awaits `production_evidence` only after a trigger is selected.

## Boundary contract
### Retro due decision
- disposition: extend
- owner: clutch/retro.py
- consumers: `Serve.check_retro`, `Retro.__call__` (drain via `_Drain._run_retro`, `clutch engine retro`)
- observable change: `select_trigger` is called with `measurements(window)` from a single pure helper; `Retro.__call__` runs `production_evidence` only when that helper returns a trigger
- compatibility: trigger kinds, `retro.*` config, report content, and the `measurements` handed to the retro spec are unchanged, because `production_evidence` still builds the report evidence
- acceptance: a forced retro still selects `forced` when merges exist; a not-due unforced call never awaits `production_evidence`
- tests: tests/unit/test_retro_due_owner.py
- post-merge source of truth: clutch/retro.py

### Serve retro check site
- disposition: extend
- owner: clutch/serve.py
- consumers: `Serve.run` maintenance loop, Recent Steps via the engine log
- observable change: `check_retro` is no longer called from the dispatch wrapper or `Serve.merge`; the `Serve.run` loop is its only caller, and the terminal-count dedupe from `retro-check-once` keeps it silent when nothing settled
- compatibility: `retro_check` phase events and outcomes are unchanged; `retro_due` and `retro_pending()` still gate dispatch and start `run_retro` as before
- acceptance: a bytecode scan of the imported `Serve` class finds exactly one `check_retro` attribute load, reachable from `Serve.run`, and none reachable from `Serve.merge` or the dispatch wrapper nested in `Serve.__init__`
- tests: tests/unit/test_serve_retro_check_site.py
- post-merge source of truth: clutch/serve.py

## Scope in / Scope out
Scope in:
- In `clutch/retro.py`, add a pure `due_trigger(window, settings, *, forced)` that returns `select_trigger(window, measurements(window), settings, forced=forced)`.
- `Retro.__call__` calls `due_trigger` first, returns early when it is `None`, and only then awaits `production_evidence` for the report.
- In `clutch/serve.py`, `Serve.check_retro` uses `due_trigger`. Remove the `await self.check_retro()` calls from the dispatch wrapper `finally` and from `Serve.merge`. Call `check_retro` once per iteration of the `Serve.run` loop, immediately before the existing `retro_task` scheduling block. Do not keep unused `measurements` or `select_trigger` imports in `clutch/serve.py` so old monkeypatches resolve; that would be a dual path.
- Update `tests/unit/test_phase_events.py` and `tests/unit/test_retro_check_vocabulary.py` where they monkeypatch names this change moves. Touch `tests/unit/test_stale_running.py` and `tests/unit/test_paved_roads.py` only if their monkeypatches of `production_evidence` stop applying.
- Update `tests/unit/test_serve_retro_check_once.py`: its setup fixture and `test_failure_retries_same_count` patch `serve.measurements` and `serve.select_trigger`; repatch them to `serve.due_trigger` so they still steer the due decision.
- Update the carried reproducer `tests/regress_serve_retro_check_once.py`: replace its `serve.select_trigger` and `serve.measurements` patches with a `serve.due_trigger` patch returning `None`.
- Add `tests/unit/test_retro_due_owner.py` and `tests/unit/test_serve_retro_check_site.py`. The site test imports `clutch.serve` and inspects compiled code objects with `dis`; it reads no repository file.

Scope out:
- Do not edit `tests/integration/serve_rig.py`. Its `observed_check` wrapper keeps working because `check_retro` keeps its name and async signature.
- Do not change the Recent Steps display.
- Do not change `_Drain._run_retro`'s own count dedupe.

## Scope fence
- clutch/retro.py
- clutch/serve.py
- tests/unit/test_phase_events.py
- tests/unit/test_retro_check_vocabulary.py
- tests/unit/test_stale_running.py
- tests/unit/test_paved_roads.py
- tests/unit/test_retro_due_owner.py
- tests/unit/test_serve_retro_check_site.py
- tests/unit/test_serve_dispatch_containment.py
- tests/unit/test_serve_retro_check_once.py
- tests/regress_serve_retro_check_once.py

## Acceptance criteria
1. `Retro.__call__(forced=False)` on a window with no trigger returns `None` without awaiting `production_evidence`. A test monkeypatches it to raise and the call still returns `None`, not an exception (`tests/unit/test_retro_due_owner.py`).
2. `Retro.__call__(forced=True)` on a window with one merge still awaits `production_evidence` once and selects `forced` (`tests/unit/test_retro_due_owner.py`).
3. `due_trigger` returns `merges` once a window's merge count reaches `retro.merges.every`, and `None` one merge below it (`tests/unit/test_retro_due_owner.py`).
4. A test imports `clutch.serve` and walks the code objects of every `Serve` function, recursing into nested code objects in `co_consts`, with `dis.get_instructions`. It finds exactly one instruction loading `check_retro`, reachable from `Serve.run`, and none reachable from `Serve.merge` or `Serve.__init__` (which holds the dispatch wrapper). It reads no repository file. A second load site fails the test (`tests/unit/test_serve_retro_check_site.py`).
5. `./dev.py test tests/unit/test_retro_due_owner.py tests/unit/test_serve_retro_check_site.py tests/unit/test_phase_events.py tests/unit/test_retro_check_vocabulary.py tests/unit/test_stale_running.py tests/unit/test_paved_roads.py tests/unit/test_serve_retro_check_once.py` exits 0.
6. The carried reproducer patches `serve.due_trigger` and no longer patches `serve.select_trigger` or `serve.measurements` (`tests/regress_serve_retro_check_once.py`).

## Verification
```
./dev.py test tests/unit/test_retro_due_owner.py tests/unit/test_serve_retro_check_site.py tests/unit/test_phase_events.py tests/unit/test_retro_check_vocabulary.py tests/unit/test_stale_running.py tests/unit/test_paved_roads.py tests/unit/test_serve_dispatch_containment.py tests/unit/test_serve_retro_check_once.py
```

## Definition of rejected
- `check_retro` is still called while `admission.merging()` is held.
- `production_evidence` still runs before a trigger is selected on an unforced call.
- `clutch/serve.py` keeps an unused `measurements` or `select_trigger` import so stale test patches resolve.
- Any edit to `tests/integration/serve_rig.py` or another hot test file.

## Time budget
- expected: 20m
- stuck: 40m