# Review: approve

The diff adds `--name` with the `Clutch <Surface> [<stem>]` session name to every ClaudeAdapter invoke and preflight probe argv, leaves every existing element in order and other adapters unchanged, and updates the pinned tests as the ticket specifies; the clutch:meta header changes come from the engine's metafill step, not from hand edits.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "8a02ff08f8c917378e99c0cfaa61f0d8465ec6e0",
  "stem": "claude-session-names",
  "reviewed_sha": "8a02ff08f8c917378e99c0cfaa61f0d8465ec6e0",
  "summary": "The diff adds `--name` with the `Clutch <Surface> [<stem>]` session name to every ClaudeAdapter invoke and preflight probe argv, leaves every existing element in order and other adapters unchanged, and updates the pinned tests as the ticket specifies; the clutch:meta header changes come from the engine's metafill step, not from hand edits.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
