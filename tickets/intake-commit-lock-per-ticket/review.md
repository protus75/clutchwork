# Review: approve

The diff makes one batched `ls-files` call and filters it by each stem's exact evidence prefix, keeps the stray refusal before any commit, keeps the outer `main_write` guard, and splits the commit lock into one inventory section and one section per stem with `_sleep(0.1)` yields between them; the new test uses the real `CommitLock` polling path, the doc and docstring match the implemented sections, and every in-repo intake caller's commit lock provides `_sleep`.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "70acb4acf6da5f7717d8a59bac62089ae003c53e",
  "stem": "intake-commit-lock-per-ticket",
  "reviewed_sha": "70acb4acf6da5f7717d8a59bac62089ae003c53e",
  "summary": "The diff makes one batched `ls-files` call and filters it by each stem's exact evidence prefix, keeps the stray refusal before any commit, keeps the outer `main_write` guard, and splits the commit lock into one inventory section and one section per stem with `_sleep(0.1)` yields between them; the new test uses the real `CommitLock` polling path, the doc and docstring match the implemented sections, and every in-repo intake caller's commit lock provides `_sleep`.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
