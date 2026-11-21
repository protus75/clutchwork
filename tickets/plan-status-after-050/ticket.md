---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
none

## Context
- docs/roadmap.md#Status

## On-demand
- docs/training-data-plan.md
- docs/stage-panels-plan.md
- docs/annotations-index-plan.md
- docs/evidence-trail-plan.md
- docs/boundary-contract-plan.md

## Goal / Why
Roadmap row 209 (`plan-status-after-050`). The 0.5.0 acceptance review found five plan documents whose `## Status` sections describe a state that no longer holds. `docs/training-data-plan.md`, `docs/stage-panels-plan.md` and `docs/annotations-index-plan.md` each say "Draft plan. Nothing in it is in effect and no ticket is authored", although their roadmap rows have merged (training rows 57-61 and 175-178, panel rows 65-68, 179, 192, 193 and 199, annotations rows 69-74, 110, 180-182, 187, 188, 191, 197 and 198). `docs/evidence-trail-plan.md` calls the evidence verbs, the per-attempt spool move and parser consolidation (rows 62-64) planned, and they merged. `docs/boundary-contract-plan.md` calls row 153 `boundary-contract-implementation-review` authored and not merged, and it merged. A reader of those plans is told the wrong thing about what exists.

After this ticket each of the five `## Status` sections says what merged (by roadmap row number and stem) and what remains open (by row), taken from the master table of the roadmap at this ticket's base commit.

## Boundary contract
none
- reason: documentation corrections without behavior change; only the `## Status` sections and their `clutch:meta` headers of five plan documents change

## Scope in / Scope out
Scope in: for each of the five documents, rewrite only the `## Status` section so each sentence is true against the roadmap's master table at the base commit. A row is merged when its stem is struck through in that table; an open row is one that is not. Name merged rows by number and stem and open rows by number, for example the open rows of the training plan are those with Owner `training` that are not struck. Keep the "Written ... at commit ..." provenance sentence of each document as it is. Then run `uv run clutch meta refresh <doc>` on each of the five documents, changing nothing else in its header.

Scope out: every other section of the five documents, the roadmap, the other plan documents, and any code.

## Scope fence
- docs/training-data-plan.md
- docs/stage-panels-plan.md
- docs/annotations-index-plan.md
- docs/evidence-trail-plan.md
- docs/boundary-contract-plan.md

## Acceptance criteria
1. `uv run clutch meta check docs/training-data-plan.md docs/stage-panels-plan.md docs/annotations-index-plan.md docs/evidence-trail-plan.md docs/boundary-contract-plan.md` exits 0.
2. The `## Status` section of each of the five documents, read in `git diff main`, names its merged rows by number and stem and its open rows by number, and none of the five still says "Nothing in it is in effect", "no ticket is authored", "remain planned" or that row 153 is "not merged". A reviewer checks each named row against the roadmap's strike-throughs; no test can decide this.
3. `git diff main --stat` lists only the five fenced documents.

## Verification
```
uv run clutch meta check docs/training-data-plan.md docs/stage-panels-plan.md docs/annotations-index-plan.md docs/evidence-trail-plan.md docs/boundary-contract-plan.md
```

## Definition of rejected
A row named merged that is not struck in the roadmap, or named open that is struck; any section other than `## Status` changed; a standing test pinning plan text; a file outside the fence changed.

## Time budget
- expected: 15m
- stuck: 30m
