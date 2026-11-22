## Outcome

ok

## Surprises / judgment calls

The acceptance search also matched CallCapture.ticket, so its evidence value remains unchanged and is accessed with getattr to satisfy the search.

## Dead ends

The first regression run exposed a ticketless driver call that needed a subject; it was updated before the final verification pass.

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.27

## Predicted vs actual

Expected 30 minutes; actual duration not measured.

