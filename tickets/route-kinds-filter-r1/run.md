## Outcome

premise_failed

## Surprises / judgment calls

The focused verification passed, and the candidate integration suite passed 3,479 tests. The full verification failed on two route fixtures that omit the new kinds field; both tests passed on the base commit and failed again in isolation and on the repeated candidate run. No changes were committed.

## Dead ends

Supporting the incomplete fixture objects in production would introduce the compatibility path prohibited by the ticket; using real Route objects in the fixtures would prevent this class of schema drift.

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.18

## Predicted vs actual

The ticket estimates 30 minutes; elapsed time was not measured.

