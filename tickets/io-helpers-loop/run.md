## Outcome

premise_failed

## Surprises / judgment calls

The existing notification tests rely on the command recording each delivery and returning a failure when notify-fails exists; FakeExec.run only records argv and returns one fixed result.

## Dead ends

Checked the notification consumers and shared fake for an existing dispatch seam; none is available, and the ticket explicitly requires stopping when a shared fake lacks needed behavior.

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.27

## Predicted vs actual

none

