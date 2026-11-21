---
state: confirmed
source: human
priority: P0
kind: chore
---

## Depends on
- none

## Runs before
- training-export-ship-gate
- meta-refresh-commit-lock

## Context
- docs/roadmap.md#Status

## Goal / Why
`uv run clutch meta check docs/roadmap.md` reports `drifted`: the owner's 2026-11-21 edits that withdrew rows 173 and 174 and their 0.4.0 ship clauses were committed (`cf8cd1fe`) without refreshing the file's `clutch:meta` block, because `meta refresh` refused while the drain held the writer lock. The 0.5.0 gate block runs `uv run clutch meta check docs clutch/docs tests`, so the gate fails on this file whatever else passes. After this ticket the block's `verified` and `hash` match the file and `meta check` reports nothing for it.

## Boundary contract
none
- reason: metadata only; regenerating the `clutch:meta` block of docs/roadmap.md with the unchanged `clutch meta refresh` generator

## Scope in / Scope out
Scope in:
- In the worktree, run `uv run clutch meta refresh docs/roadmap.md` and commit the result. Only the `verified` and `hash` lines of the metadata block change.
Scope out:
- Every other line of docs/roadmap.md, other files, and the lock behavior of `meta refresh` (delivered by `meta-refresh-commit-lock`).

## Scope fence
- docs/roadmap.md

## Acceptance criteria
1. `uv run clutch meta check docs/roadmap.md` exits 0 with no finding for docs/roadmap.md, not `drifted`.
2. `git diff main -- docs/roadmap.md` (a one-time review check) changes only the `verified:` and `hash:` lines.

## Verification
```
uv run clutch meta check docs/roadmap.md
```

## Definition of rejected
Any change to docs/roadmap.md beyond the metadata block's `verified` and `hash` lines.

## Time budget
- expected: 3m
- stuck: 6m
