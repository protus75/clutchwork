# Review: approve

The diff meets every acceptance criterion and stays inside the fence: the scheduler now starts each run as its own task and returns once it holds a slot, the slot cap is checked before selection, failures are raised exactly once through raise_failure/dispatch_next/close, serve refills slots while busy (but not while an exclusive section is held or waiting) and checks for run failures before its pause and stop guard, cleanup closes the scheduler after the workers stop and re-raises its failure, and the tests and docs are updated to match.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "dc03f8f9124fe4ff4c925fa5e0e4070563fcaa4c",
  "stem": "serve-dispatch-returns-on-slot",
  "reviewed_sha": "dc03f8f9124fe4ff4c925fa5e0e4070563fcaa4c",
  "summary": "The diff meets every acceptance criterion and stays inside the fence: the scheduler now starts each run as its own task and returns once it holds a slot, the slot cap is checked before selection, failures are raised exactly once through raise_failure/dispatch_next/close, serve refills slots while busy (but not while an exclusive section is held or waiting) and checks for run failures before its pause and stop guard, cleanup closes the scheduler after the workers stop and re-raises its failure, and the tests and docs are updated to match.",
  "findings": [],
  "spec_version": "1.8",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
