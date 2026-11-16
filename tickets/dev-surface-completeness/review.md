# Review: approve

The diff meets every acceptance criterion: the full suite runs as a guarded `tests/unit` run then an unguarded `tests/integration` run, and `test <args>` adds `-p clutch.testguard` only when every named test path is under `tests/unit`; the new unit tests fake `subprocess.run` and cover each listed case, the section 2.2 table rows pass the doc check, and only fenced files change.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "7a6c70dd2822374f69654a60fbc8a3cb1c456020",
  "stem": "dev-surface-completeness",
  "reviewed_sha": "7a6c70dd2822374f69654a60fbc8a3cb1c456020",
  "summary": "The diff meets every acceptance criterion: the full suite runs as a guarded `tests/unit` run then an unguarded `tests/integration` run, and `test <args>` adds `-p clutch.testguard` only when every named test path is under `tests/unit`; the new unit tests fake `subprocess.run` and cover each listed case, the section 2.2 table rows pass the doc check, and only fenced files change.",
  "findings": [],
  "spec_version": "1.5",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
