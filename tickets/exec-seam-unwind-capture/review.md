# Review: approve

The diff now builds and attaches `process_capture` (bytes already read plus the `_kill_and_wait` remainder) on every unwind in `SubprocessExec.run`, keeps the exception type and the consumer-error chaining, updates the `GroupExec` docstring and host-contract.md, and adds the required real-child integration tests and fake-driven unit tests, all within the scope fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "188e4238bbc8bfe84710ec6a8fba4606a3f6e540",
  "stem": "exec-seam-unwind-capture",
  "reviewed_sha": "188e4238bbc8bfe84710ec6a8fba4606a3f6e540",
  "summary": "The diff now builds and attaches `process_capture` (bytes already read plus the `_kill_and_wait` remainder) on every unwind in `SubprocessExec.run`, keeps the exception type and the consumer-error chaining, updates the `GroupExec` docstring and host-contract.md, and adds the required real-child integration tests and fake-driven unit tests, all within the scope fence.",
  "findings": [],
  "spec_version": "1.7",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
