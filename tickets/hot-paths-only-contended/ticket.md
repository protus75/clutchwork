---
state: draft
source: human
priority: P2
kind: bug
---

## Depends on
- none

## Context
- clutch/observe.py::_hot_paths
- tests/unit/test_observe_hot_paths.py
- tests/integration/test_hot_paths_snapshot.py
- tests/regress_already_satisfied.py

## On-demand
- clutch/help.py

## Goal / Why
The `hotPaths` snapshot field (`clutch view snapshot`, drawn by the extension's Tickets view) lists the ten paths fenced by the most unsettled tickets. Today it lists a path fenced by one ticket, so with two unsettled drafts the view shows ten rows of `<path>: 1` (`README.md: 1`, `clutch/__main__.py: 1`, ...), which is noise: one ticket fencing a path is no contention. After this ticket `_hot_paths` returns only paths fenced by two or more unsettled tickets, so with no contention the field is `[]` and the view shows no hot-path rows. Why: the panel exists to show where tickets will collide when planning splits; a count of 1 hides that signal behind a list that is never empty.

The extension is unchanged: `vscode-clutchwork/media/view.js` already maps whatever list the snapshot carries, and an empty list draws no rows.

## Boundary contract
### Hot paths snapshot field
- disposition: extend
- owner: clutch/observe.py
- consumers: `snapshot()` in clutch/observe.py and the Tickets view in vscode-clutchwork/media/view.js, which draws the list as given
- observable change: `hotPaths` omits every entry whose `count` is 1; entries keep the order (count descending, then path), the cap of ten, and the `{"path", "count"}` shape
- compatibility: restores the field's documented meaning, the paths fenced by the most unsettled tickets; the field name, entry shape, ordering, closed-ticket exclusion and `tickets/<stem>` outbox exclusion are preserved
- acceptance: a path fenced by one ticket is absent and a path fenced by two is present with count 2
- tests: tests/unit/test_observe_hot_paths.py, tests/integration/test_hot_paths_snapshot.py, tests/regress_hot_paths_contended.py
- post-merge source of truth: clutch/observe.py

## Scope in / Scope out
In: `_hot_paths` in clutch/observe.py drops entries whose count is below 2, applied before the top-ten cut so ten contended paths are never pushed out by uncontended ones. The `hotPaths` help entry in clutch/help.py (`TOPICS["hotPaths"]`, `what` line) says the list shows paths fenced by two or more unsettled tickets. tests/unit/test_observe_hot_paths.py: `test_counts_order_and_distinct_entries` expects only the `a.py` (3) and `b.py` (2) rows, and `test_outbox_and_top_ten` is rewritten so twelve paths shared by two tickets still cap at ten and a path fenced by one ticket is absent. tests/integration/test_hot_paths_snapshot.py: the `open` ticket shares `open.py` with a second open ticket so the expectation becomes `[{"path": "open.py", "count": 2}]`, and the closed and rejected tickets still add nothing.

Create `tests/regress_hot_paths_contended.py`, the carried reproducer, following the shape of `tests/regress_already_satisfied.py`. It builds two in-memory `Ticket`s whose fences share no path and calls `clutch.observe._hot_paths` (which exists at base). It prints only `{"regression_result": "pass"}` and exits 0 when the result is `[]`; prints `{"regression_result": "defect"}` and exits 1 when any entry has count 1; on an exception prints `{"regression_result": "error"}` to stdout, the traceback to stderr, and exits 2.

Out: the extension JavaScript, `docs/how-clutch-works.md` (it does not describe the field's rows), the snapshot shape, and the unedited-skeleton row that also shows in the view (a separate problem).

## Scope fence
- clutch/observe.py
- clutch/help.py
- tests/unit/test_observe_hot_paths.py
- tests/integration/test_hot_paths_snapshot.py
- tests/regress_hot_paths_contended.py

## Acceptance criteria
1. `_hot_paths` over tickets that fence `a.py` three times, `b.py` twice and `c.py` once returns exactly the `a.py` and `b.py` entries, never a `c.py` entry with count 1, checked by `./dev.py test tests/unit/test_observe_hot_paths.py`.
2. `_hot_paths` over twelve paths each fenced by two tickets returns ten entries, and over tickets sharing nothing returns `[]`, not ten rows of count 1, checked by `./dev.py test tests/unit/test_observe_hot_paths.py`.
3. `observe.snapshot` returns `hotPaths` equal to `[{"path": "open.py", "count": 2}]` for two open tickets fencing `open.py` plus a closed and a rejected ticket, and `[]` for a single open ticket, checked by `./dev.py test tests/integration/test_hot_paths_snapshot.py`.
4. The help entry for `hotPaths` and its doc link stay valid, checked by `./dev.py test tests/unit/test_help.py tests/integration/test_help.py`.
5. The carried reproducer prints `{"regression_result": "pass"}` on the branch head, checked by `uv run python tests/regress_hot_paths_contended.py`.

## Verification
```
./dev.py test tests/unit/test_observe_hot_paths.py tests/integration/test_hot_paths_snapshot.py tests/unit/test_help.py tests/integration/test_help.py
uv run python tests/regress_hot_paths_contended.py
```

## Definition of rejected
- `_hot_paths` still returns an entry with count 1.
- The filter is applied after the top-ten cut, or in `vscode-clutchwork/` JavaScript instead of Python.
- Any change to the snapshot field name, entry shape or ordering.

## Time budget
- expected: 12m
- stuck: 24m

## Regression
```
uv run python tests/regress_hot_paths_contended.py
```
- carries: tests/regress_hot_paths_contended.py
