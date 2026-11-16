## Outcome

premise_failed

## Surprises / judgment calls

The ticket verification passed 836 tests and the unit coverage, lint, and format gates passed. The full integration gate failed two wrong-stem custody cases; both passed on the base commit and failed again in isolation on the candidate. The exact ticket verification could not run on the base because its new test files do not exist there. checkpoint._history remains unchanged because it validates a history of keys. No changes were committed.

## Dead ends

Dropping the ticket filter as required accepts a completion whose key names the requested stem but whose ticket field names another stem; the existing custody tests require rejection.

## Second problems filed

- box-000558-9224a832: docs/roadmap.md contains statements about the old lookup implementations that the proposed change would make stale.

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.15

## Predicted vs actual

Ticket budget: 45 minutes expected, 90 minutes stuck; actual time not measured.

