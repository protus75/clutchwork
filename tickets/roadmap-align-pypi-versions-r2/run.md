## Outcome

premise_failed

## Surprises / judgment calls

The specified formula maps 1.9.0 to 1.10.0, not 2.0.0; with the existing fixture, choose() finds no 1.10.0 section and selects the first release instead.

## Dead ends

none

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.29

## Predicted vs actual

The ticket budgets 20 minutes; inspection identified the contradiction before implementation.

