## Outcome

ok

## Surprises / judgment calls

Admission state is sampled once per loop to preserve idle supervision order; retaining the old await was rejected because it serializes runs.

## Dead ends

Corrected a coroutine-shaped cleanup fake and an accidental settlement wait in the migrated cancellation test before final verification.

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-sol
- spec: implement 2.20

## Predicted vs actual

55 minutes expected; approximately 12 minutes actual.

