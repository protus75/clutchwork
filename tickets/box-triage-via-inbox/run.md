## Outcome

premise_failed

## Surprises / judgment calls

The focused verification passed with 124 tests. The full unit gate had 11 failures because existing idle-loop fixtures lack the control inbox required by the new calls; those same four test files passed on the base commit. The exact ticket verification could not run on the base because its three new test files do not exist there. The integration gate exposed a shared-call ownership issue, which was fixed within scope and verified by its focused tests.

## Dead ends

none

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.17

## Predicted vs actual

none

