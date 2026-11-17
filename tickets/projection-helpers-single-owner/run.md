## Outcome

ok

## Surprises / judgment calls

All ticket verification commands passed. The full integration gate failed on test_usage_and_independent_peak_memory, and the same test failed on the untouched base. Keeping the existing selections and moving only the duplicated operations was the minimum change.

## Dead ends

none

## Second problems filed

- box-000712-467c38bd: The full integration gate's test_usage_and_independent_peak_memory fails its memory threshold on both the candidate and base commit.
- box-000713-76c554cc: docs/roadmap.md retains descriptions of helper duplication removed by this change and is outside the scope fence.

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.17

## Predicted vs actual

Expected 25 minutes; actual time was not measured.

