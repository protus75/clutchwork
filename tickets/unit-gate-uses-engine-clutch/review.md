# Review: approve

The diff changes the unit argv prefix in config.yaml and the host-contract doc, puts the engine interpreter's directory first on PATH only in run_host_command (handling a missing or empty PATH with no stray separator), updates only the two required PATH expectations, adds the requested unit test and doc sentence, and stays inside the scope fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "0aad9c7ea09e703005a32a026c1e3685b7797d1c",
  "stem": "unit-gate-uses-engine-clutch",
  "reviewed_sha": "0aad9c7ea09e703005a32a026c1e3685b7797d1c",
  "summary": "The diff changes the unit argv prefix in config.yaml and the host-contract doc, puts the engine interpreter's directory first on PATH only in run_host_command (handling a missing or empty PATH with no stray separator), updates only the two required PATH expectations, adds the requested unit test and doc sentence, and stays inside the scope fence.",
  "findings": [],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
