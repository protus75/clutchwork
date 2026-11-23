# Review: approve

The diff meets every acceptance criterion: accept now edits the roadmap inside `commit_edit`, rebuilds the header with the same `meta._files`, `parse`, `generated` and `compose` steps that `meta.refresh` uses, refuses a malformed block before writing, keeps the `only=[roadmap.ROADMAP]` path and skips the commit when no rows are added, and the tests cover the meta-clean commit, the malformed refusal and the no-commit case.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "ce3dd66bf047655715fe7a48a68e69bcfc62dff7",
  "stem": "roadmap-accept-meta-refresh",
  "reviewed_sha": "ce3dd66bf047655715fe7a48a68e69bcfc62dff7",
  "summary": "The diff meets every acceptance criterion: accept now edits the roadmap inside `commit_edit`, rebuilds the header with the same `meta._files`, `parse`, `generated` and `compose` steps that `meta.refresh` uses, refuses a malformed block before writing, keeps the `only=[roadmap.ROADMAP]` path and skips the commit when no rows are added, and the tests cover the meta-clean commit, the malformed refusal and the no-commit case.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
