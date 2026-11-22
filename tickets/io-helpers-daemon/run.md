## Outcome

ok

## Surprises / judgment calls

Renamed private hub reachability helpers to satisfy the definition scan while preserving their assertions; retained composition’s scheduler import_closure. Final sequential verification: 24 helper unit cases, 2032 unit tests, and 296 integration tests passed. Untouched base: 294 integration passes; skips unchanged at 3339. All 26 mutation checks caught their intended defects; lint and formatting passed.

## Dead ends

A direct extraction would retain forbidden I/O, so the helpers required fake-seam rewrites.

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-sol
- spec: implement 2.27

## Predicted vs actual

30m expected; actual elapsed time was not tracked.

