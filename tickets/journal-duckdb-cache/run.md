## Outcome

ok

## Surprises / judgment calls

The cache rebuilds when an earlier segment grows so event sequence remains in segment order; reversing sequence order caused the fold-equivalence test to fail. The simpler in-memory projection would not survive across processes.

## Dead ends

The initial schema used unquoted offset, which DuckDB treats as a reserved word; quoting it fixed the targeted tests.

## Second problems filed

- box-000797-beddc761: docs/annotations-index-plan.md still describes DuckDB as a future dependency added by another ticket; it is outside the scope fence.

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.18

## Predicted vs actual

Ticket estimate: 25 minutes; elapsed time was not measured.

