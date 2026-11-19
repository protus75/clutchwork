# Review: approve

The diff runs the drain driver pass as a single background task: a new pass starts only when no pass is running, a failed pass raises at the next loop or at the end of `run`, `run` waits for a running pass through `_await_controlled` without hiding an exception already raised, and the wait at the idle exit makes sure authored tickets and the last settle's pass are handled before `run` returns, all within the fence and with tests covering criteria 1-6.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "cd72e2b633a50bb8302698b314540277a4fec93b",
  "stem": "dispatch-during-driver-pass-drain",
  "reviewed_sha": "cd72e2b633a50bb8302698b314540277a4fec93b",
  "summary": "The diff runs the drain driver pass as a single background task: a new pass starts only when no pass is running, a failed pass raises at the next loop or at the end of `run`, `run` waits for a running pass through `_await_controlled` without hiding an exception already raised, and the wait at the idle exit makes sure authored tickets and the last settle's pass are handled before `run` returns, all within the fence and with tests covering criteria 1-6.",
  "findings": [],
  "spec_version": "1.7",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
