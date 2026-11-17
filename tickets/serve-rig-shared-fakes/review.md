# Review: approve

The diff makes `serve_rig.until` delegate to `fakes.until` and keeps the old error message, gets `turn` from `tests.fakes` with the same pacing (3 clock advances at polls 1, 21 and 41 when the predicate turns true on poll 42), and adds tests for delegation, pacing and timeout translation, all inside the scope fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "c3934ae3946e57f1d22bb9e3c9facf1038de9e6d",
  "stem": "serve-rig-shared-fakes",
  "reviewed_sha": "c3934ae3946e57f1d22bb9e3c9facf1038de9e6d",
  "summary": "The diff makes `serve_rig.until` delegate to `fakes.until` and keeps the old error message, gets `turn` from `tests.fakes` with the same pacing (3 clock advances at polls 1, 21 and 41 when the predicate turns true on poll 42), and adds tests for delegation, pacing and timeout translation, all inside the scope fence.",
  "findings": [],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
