---
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
source: box:roadmap_row
state: confirmed
---

## Depends on
none

## Context
- docs/upstream-issue-plan.md#Status
- docs/parallel-tickets-plan.md#Status
- docs/gemini-graphics-refactor-plan.md#Status
- docs/evidence-trail-plan.md#Status

## Goal / Why
The Status sections of `docs/upstream-issue-plan.md`, `docs/parallel-tickets-plan.md` and `docs/gemini-graphics-refactor-plan.md` each say "Draft plan. Nothing in it is in effect and no ticket is authored." That is now false: `clutch/issue.py` (the `clutch issue` verb) has merged, the `CLAUDE.md` do-not-grow list (hot test files rule) has merged, and `clutch/providers.py::GeminiAdapter` has merged. After this ticket each of the three Status sections names what merged and what remains, in the style of the Status section in `docs/evidence-trail-plan.md`, so the next audit starts clean (roadmap section 1). This replaces merged row 124, which fixed only the driver and evidence plans.

## Scope in / Scope out
Scope in: rewrite only the Status paragraph of each of the three plan files. Each new paragraph names what merged (with the module or file that carries it), names what remains open or planned, and keeps the existing written/revised commit sentence. Before writing, read the Roadmap section and body of each plan to see which parts are merged and which are not. State only facts that the repo shows. Do not claim a part merged unless its file exists.
Scope out: every other section of these plans, and all code and tests.

## Scope fence
- docs/upstream-issue-plan.md
- docs/parallel-tickets-plan.md
- docs/gemini-graphics-refactor-plan.md

## Acceptance criteria
1. The `## Status` section of each of the three fenced plans no longer contains the phrase `Nothing in it is in effect`; check with `grep -c "Nothing in it is in effect" docs/upstream-issue-plan.md docs/parallel-tickets-plan.md docs/gemini-graphics-refactor-plan.md` printing `0` for every file.
2. `docs/upstream-issue-plan.md` Status mentions `clutch/issue.py`; `docs/parallel-tickets-plan.md` Status mentions the `CLAUDE.md` do-not-grow list; `docs/gemini-graphics-refactor-plan.md` Status mentions `GeminiAdapter`; check with `grep -c` for each name inside its own file, each count at least `1`.
3. Each Status section also names what remains, with a word `remains`, `remain`, `planned` or `open`; check by reading the three paragraphs with `grep -A3 "^## Status"`.
4. Only the three fenced files change; check with `git diff --name-only main...HEAD` listing exactly those three paths, not `docs/roadmap.md` or any file under `tests/`.

## Verification
```
./dev.py test tests/unit/test_readme.py
```

## Definition of rejected
A Status section that claims something merged that has not, or that omits what remains; any edit outside the Status paragraphs; any edit to a file outside the fence.

## Time budget
- expected: 10m
- stuck: 20m
