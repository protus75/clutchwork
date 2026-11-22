## Outcome

ok

## Surprises / judgment calls

The final sequential verification passed: the reproducer returned pass and all 57 tests passed. Under concurrent test load, earlier candidate runs timed out on admission cases; the base comparison reproduced the precheck failure and host-loop setup failures. The injected-delay reproducer confirmed that the old stop limit cancels the serve task. A suggestion was filed to assess a broader deadline lint.

## Dead ends

Increasing timeout values was rejected because it would only move the load threshold.

## Second problems filed

- box-001071-979fce43: Under concurrent test load, the base precheck admission test exceeds its wall-clock deadline.

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.25

## Predicted vs actual

The ticket estimated 25 minutes expected and 50 minutes stuck; elapsed time was not measured.

