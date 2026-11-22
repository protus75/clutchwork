## Outcome

ok

## Surprises / judgment calls

The base and candidate integration runs both reported 297 passed and 3341 skipped. Final verification passed: 6 helper tests, 2091 unit tests, and 297 integration tests; the shared-fake adoption checks also passed. The existing rig already confined its writes to the caller-provided root and did not invoke git or a process. The engine owns run.md, so these counts are reported here for its run record. The simpler approach was to move the rig unchanged; the only body adjustment was a local clock alias to satisfy the ticket's grep criterion.

## Dead ends

An initial early-wakeup mutation exposed an assertion that checked task scheduling rather than the deadline future; the assertion was corrected and the mutation was detected.

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.27

## Predicted vs actual

Expected 20 minutes; actual time was not measured.

