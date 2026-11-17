---
state: confirmed
source: box:suggestion
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/roadmap.py::choose
- clutch/roadmap.py::refile_row
- clutch/roadmap.py::author_ahead
- tests/integration/test_roadmap_refile.py

## Goal / Why
Author declines any stem that appears on any journal event (`event.ticket == stem` in `clutch/author.py`). `choose` treats a stem as used only when `last_states` has a state for it. A row whose stem appears only in non-transition events, such as the requisition-review events of a refused split proposal or of the row's own earlier declined Author attempt, is therefore chosen as ready and then declined on every attempt. `author_ahead` re-files declined rows under the unchanged `row.stem`, so the re-files cannot succeed. They burn the supervise cap, and the release gate stays blocked until someone edits the roadmap by hand. This happened to row 114 (`supervise-idle-point`, named by the review of a refused split proposal of `supervise-every-route`; declined-box-000635, declined-box-000636 and declined-box-000637; renamed by hand in b773e418, reverted by the driver's 3d7f806e, and renamed again in 11c70646). It also happened to row 21 (`test-fakes-and-conftest`, named by the requisition review of its first Author attempt, box-000559, on 2026-11-16). Its re-files declined-box-000639 and declined-box-000644 alternated between `already named in the journal` and, when Author renamed the stem to escape it, `roadmap row requires stem`, until the row was split by hand in 7379d55e. Before that split, row 105 named row 21 by its stem in `Depends on`. A rename that left that cell alone would make `choose` skip row 105 forever with no wait, because the old stem is neither a row stem nor settled. After this ticket, `author_ahead` renames such a ready row to a fresh `-rN` stem before filing it, so the row recovers unattended.

## Scope in / Scope out
Scope in:
- Add a pure helper `fresh_stem(stem, taken)` in `clutch/roadmap.py`. It returns `<base>-rN` with the smallest N >= 1 such that the result is not in `taken`. `base` is `stem` with any trailing `-rN` removed.
- In `author_ahead`, compute the set of stems named by any journal event. Before building the candidates, rewrite each ready row whose stem is in that set and has no state in `states` with `refile_row` and `fresh_stem`, and commit it as `clutch(roadmap): refile <old> as <new>`, as the rejected path does. The renamed rows are the ones filed.
- The `taken` set that `author_ahead` passes to `fresh_stem` is the union of: every stem named by any journal event, every stem of every roadmap row, and every stem that has a `tickets/<stem>/` path in the checkout's tracked files. Each new stem is added to `taken` before the next row is renamed, so two renamed rows never get the same stem. This matches Author's refusals (stem already exists, already named in the journal), so a renamed row is not declined again.
- `refile_row` also replaces the renamed row's old stem token with the new stem token in the `Depends on` cell of every other row, so a row that depends on the renamed stem follows it. Both rename paths get this through `refile_row`.
- The rejected path mints its new stem with `fresh_stem(row.stem, taken)` instead of `-r{count + 1}`, so every `-rN` stem comes from one rule. Its re-file cap logic is unchanged.

Scope out: `choose`'s signature and wait rules, `clutch/author.py`, and the docs. The deeper cause is that two code paths each decide whether a stem is used. Unifying them is a separate cause ticket.

## Scope fence
- clutch/roadmap.py
- tests/unit/test_roadmap_named_stem.py
- tests/integration/test_roadmap_named_stem.py

## Acceptance criteria
1. `fresh_stem('supervise-idle-point', {'supervise-idle-point'})` returns `'supervise-idle-point-r1'`, not the input stem, checked by `./dev.py test tests/unit/test_roadmap_named_stem.py`.
2. `fresh_stem('x-r1', {'x', 'x-r1'})` returns `'x-r2'`, not `'x-r1'` and not `'x-r1-r1'`, checked by `./dev.py test tests/unit/test_roadmap_named_stem.py`.
3. With a journal where a ready row's stem appears only on a signal event (no state transition), `author_ahead` rewrites the roadmap row to `<stem>-r1`, commits it, and files the message with the new stem. It does not file the old stem. Checked by `./dev.py test tests/integration/test_roadmap_named_stem.py`.
4. A ready row whose stem is in no journal event keeps its stem, and the roadmap file is unchanged, checked by `./dev.py test tests/integration/test_roadmap_named_stem.py`.
5. A ready row `x` whose stem is named only by a signal, while `x-r1` is already the stem of another roadmap row or has a `tickets/x-r1/` path, is renamed by `author_ahead` to `x-r2`, not `x-r1`. Checked by `./dev.py test tests/integration/test_roadmap_named_stem.py`.
6. After `author_ahead` renames a ready row `x`, whose stem is named only by a signal, to `x-r1`, a second row whose `Depends on` cell named `x` names `x-r1`, not `x`. Checked by `./dev.py test tests/integration/test_roadmap_named_stem.py`.
7. A rejected row `x` whose `x-r1` is already named in the journal is re-filed as `x-r2`, not `x-r1`. Checked by `./dev.py test tests/integration/test_roadmap_named_stem.py`.

## Verification
```
./dev.py test tests/unit/test_roadmap_named_stem.py tests/integration/test_roadmap_named_stem.py tests/integration/test_roadmap_refile.py tests/unit/test_roadmap_refile.py
```

## Definition of rejected
The branch is rejected if a row whose stem appears only in a signal event is still filed under its old stem. It is also rejected if the change touches `clutch/author.py` or adds a new wait path in `choose`. It is also rejected if a row that named the old stem in `Depends on` still names it after the rename, or if the rejected path keeps a second `-rN` rule.

## Time budget
- expected: 30m
- stuck: 60m
