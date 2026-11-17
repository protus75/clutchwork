---
state: draft
source: box:suggestion
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/author.py::goal
- clutch/author.py::AuthorGate.check
- clutch/docs/host-authoring.md#What each section is for

## Goal / Why
The Author gate refuses a roadmap-row draft whose Goal calls the work a slice of the row (the word `slice`, as both row 128 drafts wrote `Roadmap row 128, first slice:`) but whose Scope fence omits `docs/roadmap.md`, so the remaining work cannot silently drop. Roadmap driver strikes a row when its stem settles (`clutch/roadmap.py::choose`). The drafts `closed-sets-rest` and `closed-sets-rest-r1` (row 128) each called itself a first slice and named eight undelivered sets without adding a row for them, and each was rejected for it, spending a re-file. Merging either would have closed row 128 and left that work with no ticket. Only the author's choice produced the follow-up row in `closed-sets-remaining`, the one other roadmap-row ticket whose Goal says `slice`; it fences `docs/roadmap.md`, so it passes the new check.

## Scope in / Scope out
In: add a pure helper in `clutch/author.py` that takes the request's `roadmap_row`, the parsed `Goal / Why` text and the parsed `Scope fence` paths, and returns a gate finding when the request has a `roadmap_row`, the Goal matches the regex `\bslice\b` (case-insensitive), and no Scope fence path is the roadmap table file. The helper takes that path from `clutch.roadmap.ROADMAP` through a function-level import, because `clutch/roadmap.py` imports `clutch/author.py` at module level. Call it from the roadmap-row branch of the Author gate `check`. The finding's paved road reads: deliver the whole row, or fence the roadmap table file (the finding names its path) and add a follow-up row for the remaining parts in Scope in. Add one rule to `clutch/docs/host-authoring.md` under the `Scope in / Scope out` bullet stating the same. Out: a ticket for a non-roadmap request is never checked. No change to `clutch/specs/author.md`, `clutch/tickets.py` lint, or roadmap parsing. Part of the guide to update: only that bullet. The confirmed `authoring-no-standing-document-content-tests` edits the guide's `Keeping tickets apart` section, so either merge order holds.

## Scope fence
- clutch/author.py
- clutch/docs/host-authoring.md
- tests/unit/test_author_slice_follow_up.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_author_slice_follow_up.py` shows the helper returns one finding for Goal "Roadmap row 128, first slice: surfaces." with a fence lacking `docs/roadmap.md`, and returns `[]`, not a finding, once the fence lists `docs/roadmap.md`.
2. The same test shows a Goal without the word "slice" (for example "Roadmap row 128: one owner for surfaces." or "part of the row") returns `[]` with a fence lacking `docs/roadmap.md`, and that the helper gives no finding when the request has no `roadmap_row`.
3. The same test shows the finding's paved road text names `docs/roadmap.md`.
4. `./dev.py test tests/unit/test_lint_guide_parity.py tests/integration/test_lint_guide_parity.py tests/unit/test_author.py tests/unit/test_author_roadmap_row.py` exits 0, so the guide edit and existing roadmap-row author tests still pass.

## Verification
```
./dev.py test tests/unit/test_author_slice_follow_up.py tests/unit/test_lint_guide_parity.py tests/integration/test_lint_guide_parity.py tests/unit/test_author.py tests/unit/test_author_roadmap_row.py
```

## Definition of rejected
A roadmap-row draft whose Goal calls the work a slice of its row (contains the word slice) and omits `docs/roadmap.md` from its fence passes the gate, or a ticket for a non-roadmap request is refused by the new check.

## Time budget
- expected: 15m
- stuck: 30m
