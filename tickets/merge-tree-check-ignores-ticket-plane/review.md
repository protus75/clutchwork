# Review: approve

The diff extends `MergeQueue._finish` to accept tree differences under `tickets/` and in `roadmap.ROADMAP` only, failing closed on any other path or a `GitError`; both new test files cover acceptance criteria 1-4 within the scope fence, and no existing test is edited.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "fdd72877eea4c71582b0fdd437b44bacf8abfb31",
  "stem": "merge-tree-check-ignores-ticket-plane",
  "reviewed_sha": "fdd72877eea4c71582b0fdd437b44bacf8abfb31",
  "summary": "The diff extends `MergeQueue._finish` to accept tree differences under `tickets/` and in `roadmap.ROADMAP` only, failing closed on any other path or a `GitError`; both new test files cover acceptance criteria 1-4 within the scope fence, and no existing test is edited.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
