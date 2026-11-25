# Review: approve

The diff meets all five acceptance criteria and stays inside the scope fence: it persists recentRepos in clutch/mcp.py (MRU order, deduplicated, pruned, capped at 10, kept across set, OSError swallowed), puts the lifecycle diagram first in Help & Lifecycle followed by categorized helpPick rows, adds the .repo-select picker, bounds section heights with selection-free resizing, and tests it all under tmp_path and in the JS harness.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "e365a5f26eee5fbd433f9b0d166000eca18310a1",
  "stem": "mcp-dashboard-help-and-repo-picker",
  "reviewed_sha": "e365a5f26eee5fbd433f9b0d166000eca18310a1",
  "summary": "The diff meets all five acceptance criteria and stays inside the scope fence: it persists recentRepos in clutch/mcp.py (MRU order, deduplicated, pruned, capped at 10, kept across set, OSError swallowed), puts the lifecycle diagram first in Help & Lifecycle followed by categorized helpPick rows, adds the .repo-select picker, bounds section heights with selection-free resizing, and tests it all under tmp_path and in the JS harness.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
