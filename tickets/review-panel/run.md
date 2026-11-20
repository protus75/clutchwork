## Outcome

premise_failed

## Surprises / judgment calls

No files were changed. Prevent this class of failure by checking new effect-key formats against their producers and consumers when authoring the ticket.

## Dead ends

A driver-only fan-out cannot preserve the existing provider admission and evidence behavior: the provider layer owns candidate selection, evidence capture, and active-call cancellation.

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.21

## Predicted vs actual

Ticket estimate: 30 minutes; stopped during scope analysis.

