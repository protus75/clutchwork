# Review: approve

The diff routes all three running transitions through runner.mark_running with the same body and key, passes each run's ctx into MergeQueue.offer instead of overwriting queue.ctx, puts the exec call alone under a module-level HOST_COMMAND_LOCK that the test can swap out, and adds unit tests for each that fail without the change and stay inside the scope fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "7ea5ac94696a6647acafa51a67cf1cbecd8800e3",
  "stem": "parallel-dispatch-run-context",
  "reviewed_sha": "7ea5ac94696a6647acafa51a67cf1cbecd8800e3",
  "summary": "The diff routes all three running transitions through runner.mark_running with the same body and key, passes each run's ctx into MergeQueue.offer instead of overwriting queue.ctx, puts the exec call alone under a module-level HOST_COMMAND_LOCK that the test can swap out, and adds unit tests for each that fail without the change and stay inside the scope fence.",
  "findings": [],
  "spec_version": "1.7",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
