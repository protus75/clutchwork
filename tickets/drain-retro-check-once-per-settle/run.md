## Outcome

ok

## Surprises / judgment calls

The final verification pass succeeded; the selected integration tests were all skipped, and the full suite reported 289 integration tests passed and 3341 skipped. The reproducer returned defect with the original drain implementation and pass with the change. The terminal-count guard is the smallest change; modifying the loop's continue paths would leave the scheduling rule spread across multiple call sites.

## Dead ends

none

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.27

## Predicted vs actual

Ticket budget: 20 minutes expected, 40 minutes stuck; actual elapsed time was not measured.

