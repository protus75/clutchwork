## Outcome

ok

## Surprises / judgment calls

The orphan sweep retains its existing behavior of skipping when admission is busy; once entered, its exclusive gate blocks new runs.

## Dead ends

Initial gate tests needed explicit synchronization to detect admission bypassing the gate.

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.17

## Predicted vs actual

Ticket budget: 30 minutes expected, 60 minutes stuck; actual duration not measured.

