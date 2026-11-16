---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- none

## Context
- clutch/retro.py::Retro
- clutch/retro.py::RETRO_FAILED
- clutch/drain.py::_Drain._run_retro
- clutch/serve.py::Serve.check_retro
- clutch/mergequeue.py
- clutch/heartbeat.py
- clutch/__main__.py::_parser
- clutch/__main__.py::_review
- clutch/merge.py::AdmissionBoundary
- clutch/daemon.py::HeartbeatCycle
- tests/unit/test_phase_events.py
- tests/integration/test_drain.py::test_due_retro_waits_for_retry_and_precedes_next_ticket
- tests/integration/test_drain.py::requested_retro_scenario

## Goal / Why
Three pieces of engine text describe behavior the code no longer has. The `retro_check` phase also logs two different outcome vocabularies for the same phase name. These rows come from the roadmap audit (`docs/roadmap.md` section 2.1 row 14, section 3.1, section 4.2, and section 5 decision 11) and are assigned to the `docs-truth-sweep` row. This ticket is that row's code half; the document half is `docs-truth-sweep`.

- `clutch/mergequeue.py`'s module docstring says "Dormant serial admission; production routing remains in merge.py." Serve routes every merge through `MergeQueue`: `clutch/merge.py::AdmissionBoundary` runs in `daemon` mode with the queue. Only `run` and `drain` merge inline through `merge.merge`.
- `clutch/heartbeat.py`'s module docstring says "Dormant heartbeat record". Serve refreshes the heartbeat on every loop through `clutch/daemon.py::HeartbeatCycle.cycle`.
- The `review` verb's argparse help says "review a committed ticket under the lock". `clutch/__main__.py::_review` takes no `Lockfile`.
- The `retro_check` phase's `phase_end` event in `engine.log` uses one name with two vocabularies. Drain logs `ran` or `no_report` (`clutch/drain.py::_Drain._run_retro`), and serve logs `due` or `not_due` (`clutch/serve.py::Serve.check_retro`). The Recent Steps view prints the raw outcome, so the same step reads "end (no report)" under drain and "end (not due)" under serve.

After this change the docstrings and help say what the code does. `clutch/retro.py` owns one `retro_check` outcome vocabulary, `due | not_due | failed`, and drain and serve both log from it with one meaning. `due` means the pass selected a retro trigger (a fired threshold, or an operator request with a merge to report) and no earlier failure suppresses it. `not_due` means it selected none, or a failure suppresses it. `failed` means the check raised. That is the rule serve applies today.

## Scope in / Scope out
Scope in:
- `clutch/mergequeue.py`: the module docstring becomes one line saying the module is serve's serial merge admission and that `run` and `drain` merge inline through `merge.merge`. The word `Dormant` goes.
- `clutch/heartbeat.py`: the module docstring becomes one line saying serve refreshes the heartbeat file each loop while its loops are healthy, and that `is_fresh` is a read-only check for an outside watcher. The word `Dormant` goes.
- `clutch/__main__.py::_parser`: the `review` subparser's `help` becomes `review a committed ticket against merged code and journal its verdict`. No other help string changes.
- `clutch/retro.py`: add `Literal` to the `typing` import, and add `RetroCheckOutcome = Literal["due", "not_due", "failed"]` next to `RETRO_FAILED`. Give it a one-line comment saying it is the `retro_check` phase outcome for drain and serve. `Retro.__init__` sets `self.due = False`. `Retro.__call__` sets `self.due = False` on entry, then sets `self.due = True` right after it has a non-`None` trigger and `suppressing_failure(window)` is `None`, before it calls `self.driver()`. `Retro.__call__` keeps its return values and its other behavior.
- `clutch/drain.py::_Drain._run_retro`: import `RetroCheckOutcome` from `clutch.retro` at module level; `clutch.retro` does not import `clutch.drain`, so there is no cycle. The success outcome becomes `"due" if self.retro.due else "not_due"`, typed `RetroCheckOutcome`. The failure path still logs `failed` and re-raises.
- `clutch/serve.py::Serve.check_retro`: add `RetroCheckOutcome` to the existing `from clutch.retro import ...` line, and type the logged outcome with it. Its values and its due rule do not change.
- `tests/unit/test_phase_events.py::test_drain_retro_events`: the parametrization becomes `(due, result, outcome)` over `(False, None, "not_due")`, `(True, object(), "due")`, `(True, None, "due")` and `(False, RuntimeError("retro"), "failed")`. The test sets `d.retro.due` before the call. This is the one expectation in this file that changes; the preflight and serve tests stay as they are.
- `tests/integration/test_drain.py`: the two fake `Retro` classes, in `test_due_retro_waits_for_retry_and_precedes_next_ticket` and `requested_retro_scenario`, each gain the class attribute `due = False`. Drain now reads `self.retro.due` after every retro call, and without the attribute those drains raise `AttributeError`. No assertion changes and no test is added. This file is on the parallel plan's do-not-grow list, so only the forced attribute goes in.
- New file `tests/unit/test_retro_check_vocabulary.py` with the tests in the acceptance criteria.

Scope out:
- `Retro.__call__`'s return value and its callers `clutch/__main__.py::_retro` and `clutch/serve.py::Serve.run_retro`.
- Drain's call pattern. Drain still calls the retro at every between-tickets point, and it does not compute `production_evidence` a second time.
- `clutch/observe.py`, `clutch/help.py` and `vscode-clutchwork/`. They render any outcome string and map `retro_check` to `ok` or `failed` icons, so they need no change.
- `tests/integration/test_watch.py`. Its hand-built `no_report` event stands for an older `engine.log` line that `watch` must still render.
- Every document, including `docs/how-clutch-works.md`. No document states the old drain values, and the document fixes are `docs-truth-sweep`.
- The other "under the lock" help strings (`triage`, `dismiss`, `run`, `drain`). Those verbs do take the lock.

## Scope fence
- clutch/retro.py
- clutch/drain.py
- clutch/serve.py
- clutch/mergequeue.py
- clutch/heartbeat.py
- clutch/__main__.py
- tests/unit/test_retro_check_vocabulary.py
- tests/unit/test_phase_events.py
- tests/integration/test_drain.py

## Acceptance criteria
1. `tests/unit/test_retro_check_vocabulary.py::test_one_vocabulary` asserts `typing.get_args(clutch.retro.RetroCheckOutcome) == ("due", "not_due", "failed")`. Ruled out: a vocabulary that keeps drain's `ran` or `no_report`.
2. `tests/unit/test_retro_check_vocabulary.py::test_retro_records_due` is parametrized over three cases. In each, `project_window`, `production_evidence` (an `AsyncMock`), `select_trigger` and `suppressing_failure` are monkeypatched on `clutch.retro`, `Retro.failure_report` is replaced with a recorder, and the checkout is a `SimpleNamespace` whose `journal.read()` returns `[]`. There is no disk, git or process.
   - Trigger `None`: `due` is preset `True`, the call returns `None`, and `due` becomes `False`.
   - Trigger `"merges"` with a suppressing failure event: `due` is preset `True`, the call returns `None` after recording one failure report, and `due` becomes `False`.
   - Trigger `"merges"` with no failure: `due` is preset `False`. The pipeline is `SimpleNamespace()`, so `self.driver()` raises `RetroConstructionError`, which the test expects, and `due` is then `True`.
   Ruled out: `due` that is never reset, `due` set `True` whenever any trigger is selected (the suppressed case), and `due` set only after the report commits (the third case).
3. `tests/unit/test_phase_events.py::test_drain_retro_events` passes with the four `(due, result, outcome)` cases in Scope in. The `(True, None, "due")` case rules out deriving the outcome from the returned report, which is today's rule and gives `no_report`. The `(False, None, "not_due")` case rules out today's `no_report`.
4. `./dev.py test tests/unit/test_phase_events.py` still passes `test_serve_retro_events` and `test_serve_retro_failure` unchanged. That rules out changing serve's values or its due rule.
5. The second `## Verification` command exits 0: neither module docstring contains `Dormant`, and each contains `serve`. Ruled out: today's docstrings.
6. The third `## Verification` command exits 0: the `review` subparser's help contains no `lock` and equals `review a committed ticket against merged code and journal its verdict`. Ruled out: today's "under the lock".
7. `./dev.py test tests/integration/test_drain.py` exits 0 with only the two `due = False` attributes added to that file.
8. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_retro_check_vocabulary.py tests/unit/test_phase_events.py
uv run python -c "import clutch.mergequeue as m, clutch.heartbeat as h; assert all('Dormant' not in d and 'serve' in d for d in (m.__doc__, h.__doc__)), (m.__doc__, h.__doc__)"
uv run python -c "from clutch.__main__ import _parser; h = {a.dest: a.help for a in _parser()._subparsers._group_actions[0]._choices_actions}; assert h['review'] == 'review a committed ticket against merged code and journal its verdict', h['review']"
./dev.py test tests/integration/test_drain.py
./dev.py test
```

## Definition of rejected
The branch is rejected if it:
- changes `Retro.__call__`'s return values or the code of `__main__._retro` or `Serve.run_retro`;
- makes drain compute the due decision a second time, or skip a retro call it makes today;
- changes serve's outcome values or its due rule;
- reads `due` through `getattr` with a default, or adds any other fallback for a retro hook that lacks the attribute;
- adds a test to `tests/integration/test_drain.py`, or changes anything there beyond the two `due = False` attributes;
- edits `clutch/observe.py`, `clutch/help.py`, `vscode-clutchwork/` or any document;
- changes any argparse help other than `review`'s.

## Time budget
- expected: 45m
- stuck: 100m
