## Outcome

premise_failed

## Surprises / judgment calls

The current checkout has already removed the admission-wide waits from Serve.scan, Serve.watch, and verdict settlement.

## Dead ends

Inspected the existing dispatch and ticket publication paths; drain independently scans and selects ticket files, bypassing Serve’s fenced dispatch path.

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.27

## Predicted vs actual

Ticket budget: 28 minutes expected, 56 minutes stuck; scope contradiction identified during inspection.

