## Outcome

ok

## Surprises / judgment calls

Final verification: 97 passed; unit coverage gate: 1823 passed; integration: 3594 passed with one base-reproduced failure; lint, format and ticket metadata checks passed. Both reproducers pass, and the new reproducer reports defect on base. Sixteen mutations were rejected and restored. The initial config-read failure passed alone and did not recur in the further full run.

## Dead ends

Retaining mutations() would preserve the implementation-wide wait; the minimum change uses one admission state bit and the existing locks.

## Second problems filed

- box-001024-dcda882f: test_serve_admission_refusal_keeps_main_green[host-red] times out awaiting the next merge on both candidate and base.
- box-001025-93089998: An intermittent config.yaml disappearance stopped the first candidate integration run; preventing this class requires safe config restoration or coordinated reloads.
- box-001026-6e82fb44: The base integration run produced three host-loop setup errors because escape was abandoned; candidate host-loop tests passed.
- box-001027-e4b3b65e: docs/roadmap.md has metadata drift on both candidate and base.
- box-001028-010aebb2: tests/unit/test_training_triage_records.py has an empty metadata purpose on both candidate and base.

## Resolved engine/model

- provider: codex
- model: gpt-6.1-sol
- spec: implement 2.23

## Predicted vs actual

Expected 30 minutes; approximately 15 minutes including sequential gates and base comparison.

