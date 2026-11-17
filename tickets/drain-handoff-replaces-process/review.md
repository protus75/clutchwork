# Review: approve

The diff replaces the drain and serve handoffs with an in-place `ReplaceExec.replace` exec that flushes stdio first, keeps the order journaled, journal closed, lock released, then handoff, updates the fakes, docs and contract text, and adds unit and real-process tests that cover every acceptance criterion within the scope fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "8adcffed63ee77cca7564d7606923a655678dea8",
  "stem": "drain-handoff-replaces-process",
  "reviewed_sha": "8adcffed63ee77cca7564d7606923a655678dea8",
  "summary": "The diff replaces the drain and serve handoffs with an in-place `ReplaceExec.replace` exec that flushes stdio first, keeps the order journaled, journal closed, lock released, then handoff, updates the fakes, docs and contract text, and adds unit and real-process tests that cover every acceptance criterion within the scope fence.",
  "findings": [],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
