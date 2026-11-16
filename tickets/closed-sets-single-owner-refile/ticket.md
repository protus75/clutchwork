---
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
source: box:suggestion
state: confirmed
---

## Depends on
none

## Context
- tickets/closed-sets-single-home/ticket.md

## Goal / Why
Roadmap row 19 is linked to the stem `closed-sets-single-home`, which was rejected on 2026-11-16. The driver never authors a row linked to a rejected stem, and `graphics-kind` (row 49, release 0.5.0) lists that stem in its `Depends on`, so it stays blocked for good. After this change row 19 names the new stem `closed-sets-single-owner` with no authored marker, rows 19 and 49 and every other reference name that stem, and the driver offers row 19 as ready to author.

The rejected draft failed for reasons the re-filed row must state, so the next authoring does not repeat them:
1. It deleted `stages._major`, which section 2.3 calls uncalled but `stages.py` calls three times. Section 2.3 is corrected: `_major` has callers, so it becomes the single helper the other spec-major sites use.
2. `stages.ticket_blob` is imported by `clutch/serve.py`, which its fence omitted. The row names `serve.py` as a fenced importer.
3. Tier copies remain at `clutch/__main__.py` (argparse choices) and `clutch/providers.py`, and kind copies at `clutch/__main__.py` and `clutch/stats.py`. Without them `graphics-kind` cannot be one edit plus the template. The row names these sites.
4. Its `CORE_TEMPLATE` instruction could break `core_drift`. Roadmap decision 5 keeps the `--kind` list in the template for `graphics-kind`, so the row leaves the template list as it is.
5. The shared `NonBlank` strips whitespace, which would drop the final newline from `AuthorReply.ticket`. The row requires that field to keep its newline.
6. It covered 3 of the 13 sets in section 2.2 with no follow-up. The row states which sets it covers and that the rest get a named follow-up row.

## Scope in / Scope out
In `docs/roadmap.md`: change row 19's stem to `closed-sets-single-owner` and rewrite its Content cell with the six corrections above, dropping the "Authored" text and the `tickets/closed-sets-single-home/` path. Change row 49's Depends on to the new stem. Replace the stem in the "Ticket:" line under section 2.2 and in the "Tickets:" line under section 2.3. Correct the section 2.3 spec-major bullet so it no longer calls `stages.py` `_major` uncalled. Replace the stem in the "Gate to start" cell of the 0.5.0 row of the release table, changing nothing else in that row.

In `docs/gemini-graphics-refactor-plan.md`: replace the stem in the Part B summary paragraph near the top of the file, in the B1 dependency prose, and in the B1 table row.

Scope out: no code, no tests, no edit to `tickets/closed-sets-single-home/` (the rejected record stays as is), and no authoring of the new ticket (the driver does that).

## Scope fence
- docs/roadmap.md
- docs/gemini-graphics-refactor-plan.md

## On-demand
- docs/roadmap.md
- docs/gemini-graphics-refactor-plan.md

## Acceptance criteria
1. `grep -n "closed-sets-single-home" docs/roadmap.md docs/gemini-graphics-refactor-plan.md` prints nothing and exits 1, so no live reference to the rejected stem remains.
2. `grep -n "closed-sets-single-owner" docs/roadmap.md` shows row 19's stem cell, row 49's Depends on cell, and the section 2.2 and 2.3 ticket lines. `grep -n "closed-sets-single-owner" docs/gemini-graphics-refactor-plan.md` shows the B1 prose and table row.
3. `./dev.py test tests/unit/test_roadmap_table.py tests/unit/test_roadmap_status.py` passes, and `uv run clutch roadmap status` lists row 19 as ready to author, not as linked or blocked by a rejected stem.
4. Row 19's Content cell names `serve.py`, the `__main__.py` and `providers.py` tier copies, the `__main__.py` and `stats.py` kind copies, the `NonBlank` final-newline hazard for `AuthorReply.ticket`, and the follow-up for the uncovered sets; `grep -n "uncalled" docs/roadmap.md` shows no remaining claim that `stages._major` has no callers.

## Verification
```
./dev.py test tests/unit/test_roadmap_table.py tests/unit/test_roadmap_status.py tests/integration/test_roadmap_table.py
```

## Definition of rejected
The branch edits any file outside the fence, still names the rejected stem in a live reference, leaves row 19 marked authored or linked to a rejected stem, changes a section 8 ticket-table row other than 19 and 49, or changes the 0.5.0 release row beyond replacing the stem.

## Time budget
- expected: 15m
- stuck: 40m
