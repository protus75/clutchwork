## Outcome

premise_failed

## Surprises / judgment calls

The base commit passed all 5,408 tests; the candidate’s full rerun had 9 failures from two reproducible causes. The format check passed. Keeping the full integration suite as a required gate will catch these fixture and layout assumptions on future storage changes. No changes were committed.

## Dead ends

The two representative failing tests were rerun individually and both reproduced; their fixes are outside the fence.

## Second problems filed

- box-000963-e6daf0c3: docs/how-clutch-works.md still describes per-attempt captures as files under spools/, as anticipated by the separate spools-evidence-docs ticket.
- box-000964-b77f2c02: docs/roadmap.md and docs/training-data-plan.md also contain statements that the per-attempt spools layout remains in use.

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.23

## Predicted vs actual

The ticket estimated 30 minutes; elapsed time was not measured.

