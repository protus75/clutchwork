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
- clutch/docs/host-authoring.md#What each section is for

## Goal / Why
The Author gate refuses a roadmap-row draft whose Goal calls the work a slice or part of the row but whose Scope fence omits `docs/roadmap.md`, so the remaining work cannot silently drop. Roadmap driver strikes a row when its stem settles (`clutch/roadmap.py::choose`). The draft `closed-sets-rest` (row 128) called itself a slice and named eight undelivered sets without adding a row for them. Merging it would have closed row 128 and left that work with no ticket. Only the author's choice produced the follow-up row in `closed-sets-remaining`.

## Scope in / Scope out
In: add a pure helper in `clutch/author.py` that takes the parsed `Goal / Why` and `Scope fence` text and returns a gate finding when the request has a `roadmap_row`, the Goal matches the regex `\b(slice|part) of\b` (case-insensitive), and no Scope fence line names the roadmap table file. Call it from the roadmap-row branch of the Author gate `check`. The finding's paved road reads: deliver the whole row, or fence the roadmap table file (the finding names its path) and add a follow-up row for the remaining parts in Scope in. Add one rule to `clutch/docs/host-authoring.md` under the `Scope in / Scope out` bullet stating the same. Out: a ticket for a non-roadmap request is never checked. No change to `clutch/specs/author.md`, `clutch/tickets.py` lint, or roadmap parsing. Part of the guide to update: only that bullet.

## Scope fence
- clutch/author.py
- clutch/docs/host-authoring.md
- tests/unit/test_author_slice_follow_up.py
- tests/unit/test_lint_guide_parity.py
- tests/integration/test_lint_guide_parity.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_author_slice_follow_up.py` shows the helper returns one finding for Goal "first slice of row 128" with a fence lacking `docs/roadmap.md`, and returns `[]`, not a finding, once the fence lists `docs/roadmap.md`.
2. The same test shows a Goal without "slice of" or "part of" returns `[]` with a fence lacking `docs/roadmap.md`, and that the gate gives no finding when the message has no `roadmap_row`.
3. The same test shows the finding's paved road text names `docs/roadmap.md`.
4. `./dev.py test tests/unit/test_lint_guide_parity.py tests/integration/test_lint_guide_parity.py tests/unit/test_author.py tests/unit/test_author_roadmap_row.py` exits 0, so the guide edit and existing roadmap-row author tests still pass.

## Verification
```
./dev.py test tests/unit/test_author_slice_follow_up.py tests/unit/test_lint_guide_parity.py tests/integration/test_lint_guide_parity.py tests/unit/test_author.py tests/unit/test_author_roadmap_row.py
```

## Definition of rejected
A roadmap-row draft that calls itself a slice or part of its row and omits `docs/roadmap.md` from its fence passes the gate, or a ticket for a non-roadmap request is refused by the new check.

## Time budget
- expected: 15m
- stuck: 30m
