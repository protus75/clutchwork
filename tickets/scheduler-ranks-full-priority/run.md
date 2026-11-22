## Outcome

premise_failed

## Surprises / judgment calls

The focused verification passed, and all three new assertions detected their intended ordering regressions. The full unit suite failed two scheduler tests; the same command passed on the base commit with 1903 tests.

## Dead ends

The full unit suite cannot pass under the new ordering while retaining the existing scheduler test expectations.

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.27

## Predicted vs actual

Expected 12 minutes; actual time not measured.

