## Outcome

ok

## Surprises / judgment calls

With embedding disabled, the build removes an existing embeddings table. The simpler alternative of rebuilding every file was rejected because the ticket requires unchanged rows to remain untouched.

## Dead ends

none

## Second problems filed

- box-000892-547a27c7: docs/annotations-index-plan.md describes embedding file purposes, while this ticket embeds only chunk text; this was previously filed as box-000891-0fdf4294.

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.21

## Predicted vs actual

The ticket budget was 30 minutes; elapsed time was not measured.

