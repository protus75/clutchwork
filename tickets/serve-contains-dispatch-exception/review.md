# Review: approve

The diff moves the dispatch-exception terminal into one runner function that drain and serve both call, and serve now contains a ticket's `Exception` unless it is stopping, while `BaseException` and consumer failures stay fatal; the new tests and the reproducer cover every acceptance criterion, and the docs are updated, all inside the fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "a78b64d74ff1bdf436b6ff27e1708a0a2b92bfe9",
  "stem": "serve-contains-dispatch-exception",
  "reviewed_sha": "a78b64d74ff1bdf436b6ff27e1708a0a2b92bfe9",
  "summary": "The diff moves the dispatch-exception terminal into one runner function that drain and serve both call, and serve now contains a ticket's `Exception` unless it is stopping, while `BaseException` and consumer failures stay fatal; the new tests and the reproducer cover every acceptance criterion, and the docs are updated, all inside the fence.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
