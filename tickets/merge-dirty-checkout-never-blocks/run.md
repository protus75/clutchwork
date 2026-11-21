## Outcome

premise_failed

## Surprises / judgment calls

The merge tests and unit coverage gate passed, and the regression reproducer reported the defect on the merge base. The full integration run exposed a shared fixture whose filesystem fake does not contain the real checkout files used by its Git seam. The affected serve-admission test passed on the base commit and failed on the candidate. The simpler approach of restoring the owner’s entire saved file was rejected because it would discard nonconflicting ticket changes.

## Dead ends

Treating any nonempty status output as a configuration edit also misclassified fixture responses; matching porcelain records did not resolve the shared filesystem fixture mismatch.

## Second problems filed

- box-001009-707a106e: docs/how-clutch-works.md describes dirty-checkout behavior that would become stale after this change, but the ticket explicitly excludes documentation.

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.23

## Predicted vs actual

The ticket estimated 25 minutes; investigation and verification took longer because the integration gate exposed the fixture mismatch.

