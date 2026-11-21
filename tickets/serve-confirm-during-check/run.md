## Outcome

premise_failed

## Surprises / judgment calls

The held-Check test passed, but the full ticket verification was not completed successfully. An isolated run of the out-of-fence lifecycle test hung after its three-consumer fixture caused serve startup to fail.

## Dead ends

The existing test replaces the consumer tuple with three callbacks; preserving that fixture would require a compatibility path that the ticket explicitly forbids.

## Second problems filed

- box-000962-55e5afa7: docs/engine-state-db-plan.md describes verdict settlement as part of merge admission and would become stale after this change.

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.23

## Predicted vs actual

none

