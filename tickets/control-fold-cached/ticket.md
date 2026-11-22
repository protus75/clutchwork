---
state: confirmed
source: human
priority: P0
kind: bug
---

## Depends on
- none

## Runs before
- shared-fakes-guard
- shared-git-fake-integration
- shared-git-fake-unit-6
- shared-git-fake-unit-5
- shared-git-fake-unit-4
- shared-git-fake-unit-3
- shared-git-fake-unit-2
- shared-git-fake
- shared-serve-rig-config
- shared-review-script
- check-rerun-failed-only
- serve-flaky-tests-deterministic
- reconcile-spares-confirming-draft
- flake-fix-jumps-queue
- preflight-once-per-session
- serve-contains-dispatch-exception
- check-meta-fill-nested-stage
- supervisor-orders-by-depends
- gemini-provider-configured
- retry-keeps-prior-branch

## Context
- clutch/control.py::ControlInbox
- clutch/control.py::decisions
- clutch/daemon.py
- clutch/journal.py::Event

## Goal / Why
`clutch engine serve` holds one CPU core at 100% while idle (evidence file: 3 s of samples show about 100 user ticks per second, and vmstat shows no disk reads, so it is CPU, not I/O). One cause is measured: `ControlInbox._fold` iterates `decisions()` over the whole journal (49,549 events on 2026-11-21) every time it runs, costing about 5.4 ms per call against the live journal. `Control.poll()` in `clutch/daemon.py` calls `ControlInbox.consume()`, which folds twice (once through `recover()`, once directly), and `serve.dispatch` and `serve.verdicts` each poll every 100 ms. That is about 20 full-history folds per second, roughly a quarter of a core, even when no event has been appended since the last poll. The cost grows with the journal forever.

When this ticket is done, `ControlInbox` keeps the result of its last fold together with the number of journal events it covered. When `self.journal.read()` returns the same number of events as that last fold, `_fold` returns the kept result without iterating any event; when the count has grown, it folds again over the whole list as today and keeps the new result. The journal is append-only within an engine lifecycle (rolled segments stay in `read()`'s concatenation), so an unchanged count means unchanged history. The projection, the decided set and the accepted flag that callers see are unchanged.

## Boundary contract
### Control inbox fold
- disposition: extend
- owner: clutch/control.py
- consumers: `Control.poll()` in clutch/daemon.py, `ControlInbox.recover` and `ControlInbox.consume`
- observable change: a fold with no journal events appended since the previous fold iterates no events
- compatibility: restoration of the same projection, decided set and accepted flag for every journal; any appended event, including one written by `consume` itself, triggers a full refold
- acceptance: a second consume with no new events iterates zero events; an appended kill decision is visible on the next fold
- tests: tests/unit/test_control_fold_cached.py
- post-merge source of truth: clutch/control.py

## Scope in / Scope out
Scope in:
- `clutch/control.py`: in `ControlInbox`, add two private attributes initialized in `__init__` (the last fold result and the event count it covered). In `_fold`, read `events = self.journal.read()` once; if `len(events)` equals the kept count, return the kept result; otherwise fold `decisions(events)` exactly as today, keep the result and `len(events)`, and return it. Nothing else in the module changes.
- `tests/unit/test_control_fold_cached.py` (new): tests with an in-memory journal stand-in (an object whose `read()` returns a list of `clutch.journal.Event` and whose `append(type, body, ticket=, key=)` appends an `Event`), no disk.
- `tests/regress_control_fold_cached.py` (new): the reproducer named in `## Regression`, with the same in-memory journal stand-in and no disk. It builds the journal of criterion 1, calls `consume()` once, then counts the events `clutch.control.decisions` iterates during a second `consume()`. It prints `{"regression_result": "pass"}` and exits 0 when the count is 0, prints `{"regression_result": "defect"}` and exits 1 when it is greater than 0, and prints `{"regression_result": "error"}` and exits 2 when building the journal or the first `consume()` fails or the pause decision is missing. Diagnostics go to stderr.

Scope out:
- The other full-history folds in the serve loops (scheduler, storm, merge queue and the rest) and any change to `Journal` or the DuckDB journal cache.
- Poll intervals, `clutch/daemon.py` and `clutch/serve.py`.

## Scope fence
- clutch/control.py
- tests/unit/test_control_fold_cached.py
- tests/regress_control_fold_cached.py

## Acceptance criteria
1. `tests/unit/test_control_fold_cached.py` builds a journal stand-in holding 5,000 non-control signal events plus an accepted `pause` decision produced by `ControlInbox.consume` of a valid pause request (fake `files` and `read`), calls `consume()` once, then counts events iterated by `clutch.control.decisions` (wrapped with `monkeypatch`) during a second `consume()`, and asserts the count is 0, not 5,001, while `recover().pause_id` still names the pause request, run by `./dev.py test tests/unit/test_control_fold_cached.py`.
2. `tests/unit/test_control_fold_cached.py` asserts that after a valid `kill` request is consumed (appending a decision), the next `recover()` returns `kill_requested` true, not the stale cached false, run by `./dev.py test tests/unit/test_control_fold_cached.py`.
3. `tests/regress_control_fold_cached.py` prints `{"regression_result": "pass"}` and exits 0 on the branch, and prints `{"regression_result": "defect"}` with a non-zero exit at the merge base with the carried files, checked by the `## Regression` command.
4. `./dev.py test tests/unit` exits 0.

## Verification
```
./dev.py test tests/unit/test_control_fold_cached.py
./dev.py test tests/unit
```

## Regression
```
uv run python tests/regress_control_fold_cached.py
```
- carries: tests/regress_control_fold_cached.py

## Definition of rejected
- The projection, decided set or accepted flag differs from a full fold for any journal.
- The poll interval changes, or the fix lives outside `clutch/control.py`.
- The reproducer or tests write to disk.

## Time budget
- expected: 15m
- stuck: 30m
