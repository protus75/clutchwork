## Outcome

ok

## Surprises / judgment calls

The final ticket verification passed all 58 tests. The unit coverage gate passed; the full integration gate passed twice, then had one intermittent host-red timeout that passed both in isolation and in the final ticket verification. Regression passed on the candidate and reported defect on the base. Retro, supervision, box intake, maintenance, startup, and verdict settlement retain exclusive sections because their ownership is outside this ticket. Lock and overlap tests guard against recurrence; retaining the old admission gate would continue to block parallel runs.

## Dead ends

none

## Second problems filed

- box-000985-584adc0d: The full integration gate intermittently timed out in test_serve_admission_refusal_keeps_main_green[host-red]; it passed on the base verification, alone on the candidate, and in the subsequent candidate verification.
- box-000986-9d4b6377: docs/engine-state-db-plan.md describes scan and watch admission exclusion, which this change makes stale and which is outside the scope fence.
- box-000987-32be8c75: The base metadata check reports docs/roadmap.md as drifted and tests/unit/test_training_triage_records.py with an empty purpose.

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.23

## Predicted vs actual

The ticket estimated 30 minutes; elapsed time was not measured.

