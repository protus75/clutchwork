## Outcome

premise_failed

## Surprises / judgment calls

A read-only probe confirmed Time.sleep(5) remains pending after advance(4) and completes after advance(1), while FakeClock raises AttributeError for sleep. Verification suites were not run because the ticket explicitly requires stopping for missing shared-fake behavior.

## Dead ends

Replacing Time with FakeClock cannot preserve its sleep contract, and defining a replacement clock locally conflicts with the shared-fake requirement.

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-sol
- spec: implement 2.27

## Predicted vs actual

30m expected; stopped during prerequisite inspection.

