## Outcome

ok

## Surprises / judgment calls

The final sequential verification passed: 17 helper tests, 1,960 unit tests, and 289 integration tests; 3,341 integration tests were skipped, matching the base commit. The shared-fakes adoption checks also passed. Retaining the hub helpers was rejected because they depend on real git and processes.

## Dead ends

The first drain smoke test exposed that GitFake's default show result could not satisfy the committed-core check; the helper now configures the fake to read the temporary fixture's conduct file.

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.27

## Predicted vs actual

Ticket budget: 30 minutes expected, 60 minutes stuck; elapsed time not measured.

