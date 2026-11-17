# Review: approve

The diff turns the clock-based `elapsed` retro trigger into the settled-ticket trigger the ticket asks for: it counts distinct stems that reach a state in the imported `SETTLED` set, renames `RetroDays` to `RetroSettled` with no alias, updates every `select_trigger` caller and both docs, and adds tests that meet each acceptance criterion while staying inside the scope fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "95987b13c3f246b05b72ca9f2afb5d71707ce7be",
  "stem": "cadences-count-runs",
  "reviewed_sha": "95987b13c3f246b05b72ca9f2afb5d71707ce7be",
  "summary": "The diff turns the clock-based `elapsed` retro trigger into the settled-ticket trigger the ticket asks for: it counts distinct stems that reach a state in the imported `SETTLED` set, renames `RetroDays` to `RetroSettled` with no alias, updates every `select_trigger` caller and both docs, and adds tests that meet each acceptance criterion while staying inside the scope fence.",
  "findings": [],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
