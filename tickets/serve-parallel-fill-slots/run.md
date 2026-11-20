## Outcome

premise_failed

## Surprises / judgment calls

Ticket verification passed all 65 tests and the unit coverage gate passed all 1,299 tests. The full integration check failed test_production_core_unwinds_errors_and_cancellation[load]; that test passes on the base commit and fails again in isolation on the candidate. The exact ticket verification command cannot run on the base because its new test file does not exist there.

## Dead ends

Reading the live parallel configuration before selection preserves pending tickets when loading raises, but the existing integration test requires the selected ticket to have been removed before that error.

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.20

## Predicted vs actual

The ticket estimated 30 minutes; the work stopped after verification revealed the conflicting expectation.

