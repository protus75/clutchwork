# Review: approve

The diff adds the strict, fail-closed `Parallel` model under `Scheduler` with the required defaults, adds a doctor `parallel` row that appears only in the mismatch case (the provider lookup is safe because config validation already checks route references), updates exactly the named docs, help text and contract inventory rows, and puts its tests in a new tmp_path-only unit file, all inside the scope fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "5d23405b25f9ef9eda180a3880288dcd0fd90e37",
  "stem": "parallel-config",
  "reviewed_sha": "5d23405b25f9ef9eda180a3880288dcd0fd90e37",
  "summary": "The diff adds the strict, fail-closed `Parallel` model under `Scheduler` with the required defaults, adds a doctor `parallel` row that appears only in the mismatch case (the provider lookup is safe because config validation already checks route references), updates exactly the named docs, help text and contract inventory rows, and puts its tests in a new tmp_path-only unit file, all inside the scope fence.",
  "findings": [],
  "spec_version": "1.7",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
