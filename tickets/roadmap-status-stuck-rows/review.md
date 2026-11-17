# Review: approve

The diff meets every acceptance criterion and stays inside the scope fence: `choose` now puts rejected and draft linked rows in waits, callers that pass no `drafts` get the same result as before, status adds a `declined` wait line, takes declined rows out of `next:` and prints no duplicate box-derived line, `merged` reports drafts, the two verb rows in `docs/how-clutch-works.md` are updated, and the tests match the ticket.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "cc6017e0a5c741f657224d804666f5f437794e56",
  "stem": "roadmap-status-stuck-rows",
  "reviewed_sha": "cc6017e0a5c741f657224d804666f5f437794e56",
  "summary": "The diff meets every acceptance criterion and stays inside the scope fence: `choose` now puts rejected and draft linked rows in waits, callers that pass no `drafts` get the same result as before, status adds a `declined` wait line, takes declined rows out of `next:` and prints no duplicate box-derived line, `merged` reports drafts, the two verb rows in `docs/how-clutch-works.md` are updated, and the tests match the ticket.",
  "findings": [],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
