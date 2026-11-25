## Outcome

premise_failed

## Surprises / judgment calls

Both clutch_snapshot and draft prompt resolution require observe.snapshot, which calls journal_facts and opens the writable journal cache; class prevention requires a read-only snapshot path owned by the observation code.

## Dead ends

The existing snapshot has no read-only injection point, and changing its global behavior from the MCP server would not provide a safe per-call seam.

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.29

## Predicted vs actual

none

