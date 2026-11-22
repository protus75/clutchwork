# Review: approve

The diff skips an unforced drain retro check only when the journal's terminal-transition count matches the count from the last completed check, always runs forced checks, records the count only after the hook succeeds, has fakes-only tests and a reproducer covering every acceptance case, updates section 9.5 of the doc, and touches only fenced files.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "dfcfcb4f8c8c76f0dba778369d0f26d027556e49",
  "stem": "drain-retro-check-once-per-settle",
  "reviewed_sha": "dfcfcb4f8c8c76f0dba778369d0f26d027556e49",
  "summary": "The diff skips an unforced drain retro check only when the journal's terminal-transition count matches the count from the last completed check, always runs forced checks, records the count only after the hook succeeds, has fakes-only tests and a reproducer covering every acceptance case, updates section 9.5 of the doc, and touches only fenced files.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
