## Outcome

ok

## Surprises / judgment calls

The index removes an existing embeddings table when embedding is disabled. The new tests cover incremental updates, embedding failures, recovery, and extension loading.

## Dead ends

A mutation check exposed a gap in the SQL statement recorder; the recorder was corrected and the mutation was caught.

## Second problems filed

- box-000891-0fdf4294: docs/annotations-index-plan.md describes embedding files.purpose, while this ticket explicitly embeds only chunk text; that document is outside the scope fence.

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.21

## Predicted vs actual

The ticket budget was 30 minutes; elapsed time was not measured.

