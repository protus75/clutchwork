---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
- none

## Context
- clutch/observe.py::_hot_paths
- clutch/observe.py::snapshot
- vscode-clutchwork/media/view.js
- tests/unit/test_observe_hot_paths.py
- tests/integration/test_hot_paths_snapshot.py
- tests/regress_hot_paths_contended.py

## On-demand
- clutch/help.py

## Goal / Why
Today the Tickets view draws the `hotPaths` snapshot field as bare lines above the ticket rows (`clutch/__main__.py: 2`). They are not tickets, carry no heading, and are drawn with the class used for ticket status text, so they read as an error (owner report, 2026-11-20). After this ticket those lines are gone from the Tickets list. The same information, which of a ticket's fenced paths another unsettled ticket also fences, appears in that ticket's own detail: each unsettled row's `detail` gains a `Shared fence` entry listing each such path with the other tickets that fence it, and no entry when nothing is shared.

Why: a collision matters per ticket, when planning a split of that ticket, so it belongs in that ticket's detail and not in a list of paths at the top of the view.

## Boundary contract
### Shared fence information in the snapshot
- disposition: replace
- owner: clutch/observe.py
- consumers: the Tickets view in vscode-clutchwork/media/view.js and its detail pane, which already draws every `detail` entry as given
- observable change: the snapshot fields `hotPaths` and `hotPathsHelp` are removed and `_hot_paths` is replaced by a function that maps each unsettled stem to its finished `Shared fence` detail text; each non-merged row's `detail` gains a `{"heading": "Shared fence", "text": ...}` entry when that ticket shares at least one fenced path with another unsettled ticket, one line per path as `<path> (also: <stem>, <stem>)`, paths sorted, other stems sorted
- compatibility: old contract is `hotPaths`, the ten most fenced paths with counts, and `hotPathsHelp`; the replacement is the per-row `detail` entry; the only consumer of the old fields is view.js, which stops reading them in this same change; the `TOPICS["hotPaths"]` help entry is removed with the field; `tickets/<stem>` outbox paths and settled or closed tickets stay excluded as before; every other snapshot field is unchanged
- acceptance: the snapshot has no `hotPaths` key; two unsettled tickets fencing one path each show a `Shared fence` entry naming the other; an uncontended ticket shows none
- tests: tests/unit/test_observe_hot_paths.py, tests/integration/test_hot_paths_snapshot.py
- post-merge source of truth: clutch/observe.py

## Scope in / Scope out
In: replace `_hot_paths` in clutch/observe.py with `_shared_fences(tickets)`, where `tickets` is the unsettled tickets and the result maps a stem to its finished detail text, one `<path> (also: <stem>, <stem>)` line per path, paths sorted and other stems sorted, only for stems with at least one path, counting only paths another unsettled ticket also fences, with `tickets/<stem>` outbox paths and a trailing `/` handled as `_hot_paths` handles them today. `snapshot` stops emitting `hotPaths` and `hotPathsHelp` and, when the stem is in that mapping, appends `{"heading": "Shared fence", "text": <mapped text>}` before `Depends on`. docs/how-clutch-works.md line 117 (the sentence that the Tickets view shows a hot-paths table of the ten most fenced paths) is replaced by one saying each unsettled ticket's detail shows a `Shared fence` entry listing its fenced paths that another unsettled ticket also fences, with those tickets. vscode-clutchwork/media/view.js drops the `hotPaths` rows and the `...hotPaths` argument of `list.replaceChildren`. clutch/help.py drops `TOPICS["hotPaths"]`. tests/unit/test_observe_hot_paths.py is rewritten for `_shared_fences`, pinning the exact returned text for three tickets with an exclusive path, a path shared by two and a path shared by three, the outbox exclusion and `{}` for no sharing. It also gains a test that calls `observe.snapshot` with the monkeypatched seams used in tests/unit/test_snapshot_merged_cap.py:12-29, importing `dispatch_ticket` and `fake_snapshot_inputs` from tests.unit.test_menu_admission, using two open ticket stand-ins whose `scope_fence` share one path, and asserts each row's `Shared fence` detail entry text. tests/integration/test_hot_paths_snapshot.py is rewritten: two open tickets fencing `open.py` each carry a `Shared fence` entry naming the other, a lone open ticket carries none, closed and rejected tickets add nothing, and `hotPaths` is not a key of the snapshot. tests/regress_hot_paths_contended.py imports `_hot_paths` and is deleted.

Out: the verdict-decision lines, which have the same unlabeled look but belong to a different surface; the `status`-style row for them is a separate problem. Also out: the Box and Details views' code.

## Scope fence
- clutch/observe.py
- clutch/help.py
- vscode-clutchwork/media/view.js
- docs/how-clutch-works.md
- tests/unit/test_observe_hot_paths.py
- tests/integration/test_hot_paths_snapshot.py
- tests/regress_hot_paths_contended.py

## Acceptance criteria
1. `_shared_fences` over tickets that fence `a.py` three times, `b.py` twice and `c.py` once returns for each stem the exact text `a.py (also: <stems>)` plus `b.py (also: <stems>)` where it applies, and never a `c.py` line, checked by `./dev.py test tests/unit/test_observe_hot_paths.py`.
2. `_shared_fences` over tickets that share nothing returns `{}`, not one entry per fenced path, checked by `./dev.py test tests/unit/test_observe_hot_paths.py`.
3. `observe.snapshot` has no `hotPaths` or `hotPathsHelp` key, and two open tickets fencing `open.py` each have a `Shared fence` detail entry equal to `open.py (also: <other stem>)`, while a lone open ticket has none, checked by `./dev.py test tests/integration/test_hot_paths_snapshot.py`.
4. `observe.snapshot` over two unit-test ticket stand-ins sharing one fenced path gives each row the `Shared fence` entry naming the other, and a row with `scope_fence=()` none, checked by `./dev.py test tests/unit/test_observe_hot_paths.py`.
5. The help entries and their links still resolve with `hotPaths` removed, checked by `./dev.py test tests/unit/test_help.py tests/integration/test_help.py`.

## Verification
```
./dev.py test tests/unit/test_observe_hot_paths.py tests/integration/test_hot_paths_snapshot.py tests/unit/test_help.py tests/integration/test_help.py
```

## Definition of rejected
- The snapshot still carries `hotPaths`, or view.js still draws path-count lines above the ticket rows.
- The JavaScript computes which paths are shared, or builds the detail text.
- A `Shared fence` entry appears for a ticket that shares no path.

## Time budget
- expected: 20m
- stuck: 40m
