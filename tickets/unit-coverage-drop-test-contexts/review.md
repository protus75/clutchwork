# Review: approve

The diff stops the unit check from recording per-test contexts, adds a validated optional `flake_coverage_argv` that reruns only a flaky test under coverage and fails closed when it is unset or its report is malformed, moves the context parser into covmap with its own coverage config file, and updates the docs and tests the ticket names; every acceptance criterion is met inside the scope fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "c46fb1f44c92267c0390a2e4eef0c7f848f7b608",
  "stem": "unit-coverage-drop-test-contexts",
  "reviewed_sha": "c46fb1f44c92267c0390a2e4eef0c7f848f7b608",
  "summary": "The diff stops the unit check from recording per-test contexts, adds a validated optional `flake_coverage_argv` that reruns only a flaky test under coverage and fails closed when it is unset or its report is malformed, moves the context parser into covmap with its own coverage config file, and updates the docs and tests the ticket names; every acceptance criterion is met inside the scope fence.",
  "findings": [],
  "spec_version": "1.7",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
