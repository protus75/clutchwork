# Review: approve

The diff adds `_hot_paths` (count, dedupe, own-outbox drop, sort, 10-row cut) fed only by the snapshot's non-merged rows, plus `hotPaths`/`hotPathsHelp` with a valid help topic, a view.js renderer that only draws the rows, the one doc sentence, and `scope_fence=()` stand-in fixes, all inside the fence and meeting every acceptance criterion.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "4168b5cd64c34025468ec379b76d50200feda30c",
  "stem": "status-hot-paths",
  "reviewed_sha": "4168b5cd64c34025468ec379b76d50200feda30c",
  "summary": "The diff adds `_hot_paths` (count, dedupe, own-outbox drop, sort, 10-row cut) fed only by the snapshot's non-merged rows, plus `hotPaths`/`hotPathsHelp` with a valid help topic, a view.js renderer that only draws the rows, the one doc sentence, and `scope_fence=()` stand-in fixes, all inside the fence and meeting every acceptance criterion.",
  "findings": [],
  "spec_version": "1.7",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
