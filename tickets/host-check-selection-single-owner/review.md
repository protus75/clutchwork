# Review: approve

The diff meets every acceptance criterion: `triggered_hosts(tier=...)` is now the only filter for Check and both merge tiers, `gather_evidence` runs Verification and its base reruns through `run_host_command` with the same spool names and layout, a missing or invalid coverage report on an exit-0 run now fails with the required finding, the discarded base `results` read is deleted, and the doc and test changes stay inside the fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "ea33fc1454bf908d08ce10f97b0ff46eb5a9ae17",
  "stem": "host-check-selection-single-owner",
  "reviewed_sha": "ea33fc1454bf908d08ce10f97b0ff46eb5a9ae17",
  "summary": "The diff meets every acceptance criterion: `triggered_hosts(tier=...)` is now the only filter for Check and both merge tiers, `gather_evidence` runs Verification and its base reruns through `run_host_command` with the same spool names and layout, a missing or invalid coverage report on an exit-0 run now fails with the required finding, the discarded base `results` read is deleted, and the doc and test changes stay inside the fence.",
  "findings": [],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
