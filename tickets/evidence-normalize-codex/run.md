## Outcome

ok

## Surprises / judgment calls

The fixture selects the inclusive-input rule, though its counts alone do not prove that cached tokens are included. The current Claude and Codex Parsed values both appear to report total input under that rule, so the fixture does not establish a mixed-scale bug.

## Dead ends

none

## Second problems filed

- box-000606-d147480a: docs/evidence-trail-plan.md still says that nothing in clutch pins the Codex input-token basis; that statement is now stale and the file is outside the scope fence.

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.16

## Predicted vs actual

The ticket budget was 45 minutes; elapsed time was not measured.

