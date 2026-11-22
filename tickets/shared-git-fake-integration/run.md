## Outcome

premise_failed

## Surprises / judgment calls

The nine older FakeGit users were already migrated. The covmap and harvest verification command skipped all eight tests; the unit verification passed 81 tests. The adoption command passed on the untouched base but failed on the new temporary-file checks under the integration I/O guard.

## Dead ends

Attempted the required temporary-file checks in the adoption test; the integration guard blocked their writes.

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.27

## Predicted vs actual

none

