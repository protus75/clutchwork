# Review: approve

The diff changes `unwrap_fence` in place. The fence strip still runs first, text that already starts with `{` is returned unchanged, and otherwise the text is scanned with `raw_decode` for top-level objects, and the object is returned only when exactly one is found. Tests cover every acceptance case, the two existing test changes are in scope, and no doc describes the old behavior.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "5f8fbd23e9e149ff75b2806f11acc109d1af1367",
  "stem": "reply-parse-prose-before-json",
  "reviewed_sha": "5f8fbd23e9e149ff75b2806f11acc109d1af1367",
  "summary": "The diff changes `unwrap_fence` in place. The fence strip still runs first, text that already starts with `{` is returned unchanged, and otherwise the text is scanned with `raw_decode` for top-level objects, and the object is returned only when exactly one is found. Tests cover every acceptance case, the two existing test changes are in scope, and no doc describes the old behavior.",
  "findings": [],
  "spec_version": "1.7",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
