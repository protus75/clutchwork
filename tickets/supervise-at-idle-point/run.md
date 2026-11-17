## Outcome

ok

## Surprises / judgment calls

Moved last_dispatched's existing default to the class for constructor-free drain fakes; preserved unscoped terminal-call arguments and scoped refusal lifts. Prevention: lineage guards and 35 new tests reject repeat supervision and incorrect cleanup; the new module has 100% unit coverage.

## Dead ends

Reusing failure_terminal would emit an unwanted terminal, so the shared step was extracted; mutation checks required bytecode-cache invalidation before restoration checks.

## Second problems filed

- box-000648-1552cb05: docs/roadmap-driver-plan.md still describes idle supervision as planned; the implementation makes that wording stale, but the file is outside the scope fence.

## Resolved engine/model

- provider: codex
- model: gpt-6.1-sol
- spec: implement 2.16

## Predicted vs actual

45 minutes expected; approximately 16 minutes actual.

