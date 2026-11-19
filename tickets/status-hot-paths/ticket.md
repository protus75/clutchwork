---
state: confirmed
source: box:roadmap_row
priority: P3
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/observe.py::snapshot
- clutch/tickets.py::fences_overlap
- clutch/help.py
- vscode-clutchwork/media/view.js
- docs/parallel-tickets-plan.md#8. Measurement

## Goal / Why
Roadmap row 48, parallel plan section 8. After this ticket the extension snapshot carries a `hotPaths` table: the 10 fenced paths that the most unsettled tickets fence, with each path's count, and the Tickets view draws it. Today nobody can see which files make tickets collide, so nobody knows which file to split next. Parallel dispatch (rows 42-47) runs two tickets together only when their fences are disjoint, so the table shows what blocks parallelism.

Counting rule, computed in Python in the snapshot builder: a ticket is unsettled when it is in the snapshot's open rows or running (not merged, rejected, or otherwise closed). Each ticket counts once per distinct fence entry, after dropping trailing `/`. A ticket's own outbox entry (`tickets/<stem>` or a path under it) is dropped, as `fences_overlap` drops it. Rows sort by count descending, then path ascending, and are cut to 10.

## Boundary contract
### Snapshot hot-paths field
- disposition: extend
- owner: clutch/observe.py (`snapshot`)
- consumers: vscode-clutchwork/media/view.js, tests/unit/test_help.py help coverage
- observable change: the snapshot dict gains `hotPaths` (list of `{path, count}` rows, at most 10) and `hotPathsHelp` (a help topic key present in `help`). No existing key changes.
- compatibility: every existing snapshot key keeps its shape and value; the extension reader changes in the same ticket
- acceptance: counting, own-outbox exclusion, ordering, the 10-row cut and the empty case are tested on the builder
- tests: tests/unit/test_observe_hot_paths.py; help tests for the new topic
- post-merge source of truth: clutch/observe.py
### Extension drawing
- disposition: extend
- owner: vscode-clutchwork/media/view.js
- consumers: operators of the Tickets view
- observable change: view.js draws one row per `hotPaths` entry (path, count) with the help text as its tooltip. JavaScript does not count, filter, sort, or cut.
- compatibility: existing rows, header, and decisions render unchanged
- acceptance: view.js reads only `snap.hotPaths` and `snap.help[snap.hotPathsHelp]`; no counting or sorting code is added
- tests: none runnable without node; checked by review against the thin-wrapper rule, and the Python tests pin the snapshot shape view.js reads
- post-merge source of truth: vscode-clutchwork/media/view.js

## Scope in / Scope out
Scope in:
- A private builder in `clutch/observe.py` that takes the unsettled tickets and returns the `hotPaths` rows; `snapshot` calls it and adds `hotPaths` and `hotPathsHelp`.
- One help topic in `clutch/help.py` for the table: what it is, what comes before and after, linking the `docs/how-clutch-works.md` section that owns it. Edit existing help tests only where an exact topic-set assertion is forced.
- A new integration test, `tests/integration/test_hot_paths_snapshot.py`, that builds a snapshot the way `tests/integration/test_status.py` does (not editing that file or `test_watch.py`) and asserts `snap['hotPathsHelp'] in snap['help']` and that `snap['hotPaths']` is a list of `{path, count}` rows. The builder's own lines stay covered by `tests/unit/test_observe_hot_paths.py` through in-memory Ticket inputs.
- `vscode-clutchwork/media/view.js` draws the rows; `view.css` styles them only if needed.
- `docs/how-clutch-works.md`: add one sentence in the section that describes the snapshot or extension view, naming the hot-paths table. Edit only that section.
Scope out:
- `clutch view status` text output, graph code, dispatch, `fences_overlap`, and `shared_paths` handling.
- Retro proposals for conflicting paths (plan section 8, second bullet).

## Scope fence
- clutch/observe.py
- clutch/help.py
- vscode-clutchwork/media/view.js
- vscode-clutchwork/media/view.css
- docs/how-clutch-works.md
- tests/unit/test_observe_hot_paths.py
- tests/integration/test_hot_paths_snapshot.py
- tests/unit/test_help.py
- tests/unit/test_help_snapshot.py
- tests/integration/test_help.py

## Acceptance criteria
1. With three unsettled tickets fencing `a.py`, two fencing `b.py`, and one fencing `c.py`, the builder returns rows ordered `a.py` 3, `b.py` 2, `c.py` 1, checked by `./dev.py test tests/unit/test_observe_hot_paths.py`; an unsorted or insertion-order result fails it.
2. A merged or rejected ticket's fence is not counted, and a ticket that lists `a.py` and `a.py/` counts once toward `a.py`, checked by `./dev.py test tests/unit/test_observe_hot_paths.py`.
3. A ticket's own `tickets/<stem>` outbox entry produces no row, checked by `./dev.py test tests/unit/test_observe_hot_paths.py`.
4. Twelve distinct paths yield exactly 10 rows, with count ties broken by path ascending, checked by `./dev.py test tests/unit/test_observe_hot_paths.py`; no tickets yields `[]`, not `None`.
5. The built snapshot's `hotPathsHelp` value is a key of its `help` map and `hotPaths` is a list of `{path, count}` rows, checked by `./dev.py test tests/integration/test_hot_paths_snapshot.py`; a snapshot missing either key fails it.
6. `view.js` contains no sort, filter, or count over `hotPaths`, checked by review against the CLAUDE.md thin-wrapper rule at the diff.

## Verification
```
./dev.py test tests/unit/test_observe_hot_paths.py tests/integration/test_hot_paths_snapshot.py tests/unit/test_help.py tests/unit/test_help_snapshot.py tests/integration/test_help.py
```

## Definition of rejected
The branch counts, sorts, or cuts rows in JavaScript; counts settled tickets; or changes any existing snapshot key.

## Time budget
- expected: 25m
- stuck: 50m
