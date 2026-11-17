# Review: approve

The diff adds `_write_row`, which re-reads `docs/roadmap.md` and parses it again before every strike, link, refile and post-authoring link, skips the write and reports it when the row's stem or content has changed, and commits only the roadmap file; the three new tests cover acceptance criteria 1–3, and the new file and `clutch/roadmap.py` are the only paths changed, both inside the fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "27b159e9901d840de07217e2d735dd824a0b765b",
  "stem": "roadmap-fresh-write",
  "reviewed_sha": "27b159e9901d840de07217e2d735dd824a0b765b",
  "summary": "The diff adds `_write_row`, which re-reads `docs/roadmap.md` and parses it again before every strike, link, refile and post-authoring link, skips the write and reports it when the row's stem or content has changed, and commits only the roadmap file; the three new tests cover acceptance criteria 1–3, and the new file and `clutch/roadmap.py` are the only paths changed, both inside the fence.",
  "findings": [],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
