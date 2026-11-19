## Outcome

ok

## Surprises / judgment calls

Chose permitted option (b): resolve and review may nest inside the same ticket's merge stage; documented and tested stage restoration.

## Dead ends

Stage suspension violated the enforced centralized stage-event seam, so it was replaced with the permitted nesting exception.

## Second problems filed

- box-000781-0e7afd5d: Inline merge still disables merge_conflict_facts, leaving its conflict paths unmeasured, confirmed on the base commit.

## Resolved engine/model

- provider: codex
- model: gpt-6.1-sol
- spec: implement 2.17

## Predicted vs actual

30m expected; approximately 15m actual.

