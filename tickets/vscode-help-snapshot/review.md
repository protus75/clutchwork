# Review: approve

The diff meets every acceptance criterion and stays inside the scope fence: the help registry reaches the snapshot through `help_payload()`, status keys come from each branch rather than from parsed text, `next` uses each entry's `MenuEntry.command`, `engineVerbs` details come from the help map, and `stats_tree` adds tooltips only to top-level rows that have a `stat.*` topic.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "f5f1c3a0058a84dab05dc62fee2de45f59183f41",
  "stem": "vscode-help-snapshot",
  "reviewed_sha": "f5f1c3a0058a84dab05dc62fee2de45f59183f41",
  "summary": "The diff meets every acceptance criterion and stays inside the scope fence: the help registry reaches the snapshot through `help_payload()`, status keys come from each branch rather than from parsed text, `next` uses each entry's `MenuEntry.command`, `engineVerbs` details come from the help map, and `stats_tree` adds tooltips only to top-level rows that have a `stat.*` topic.",
  "findings": [],
  "spec_version": "1.5",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
