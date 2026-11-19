## Outcome

premise_failed

## Surprises / judgment calls

The ticket verification passed with 214 tests, but the full host checks failed. The base verification command could not collect because the two new test files do not exist on the base commit. The two conflicting existing tests passed individually on the base and failed individually on the candidate. Changes remain uncommitted.

## Dead ends

Direct calls to MergeQueue._admit passed the new integration cases, but the full serve path runs admission inside an already-open driver stage and fails when the model stage starts.

## Second problems filed

- box-000776-d6adbe8e: Inline merge does not record conflict paths in merge_conflict_facts, leaving the measurement gap identified in the ticket’s evidence.
- box-000777-f45df3dd: docs/parallel-tickets-plan.md describes all non-mechanical conflicts as going directly to Rework, which becomes stale when the model step lands.

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.17

## Predicted vs actual

Ticket budget: 30 minutes expected, 60 minutes stuck; elapsed time was not measured.

