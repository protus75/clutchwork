# Review: approve

The diff meets every acceptance criterion and stays inside the scope fence: keyed calls write start.json before the process starts and end.json on every exit path, the old capture writer and its numbering are gone, harvest reads its events tail from the evidence store through the FileSystem seam, per-call engine.log events carry call_key, and the required docs and tests are updated.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "952e155c7874dc360e51c668c7c725b9834881b5",
  "stem": "evidence-envelope",
  "reviewed_sha": "952e155c7874dc360e51c668c7c725b9834881b5",
  "summary": "The diff meets every acceptance criterion and stays inside the scope fence: keyed calls write start.json before the process starts and end.json on every exit path, the old capture writer and its numbering are gone, harvest reads its events tail from the evidence store through the FileSystem seam, per-call engine.log events carry call_key, and the required docs and tests are updated.",
  "findings": [],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
