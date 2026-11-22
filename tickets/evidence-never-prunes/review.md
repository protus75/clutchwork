# Review: approve

The diff removes the automatic prune from invoke and renames the setting to warn_gb with no alias; it adds a shared size_warning helper used by doctor (as a WARN row, exit still 0) and by view status, adds the writer-locked `evidence prune --to-gb N` verb with full help, updates the fenced docs, and adds tests that cover every acceptance criterion.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "679ce3761b672414be0a954a3347aeac3b6f2791",
  "stem": "evidence-never-prunes",
  "reviewed_sha": "679ce3761b672414be0a954a3347aeac3b6f2791",
  "summary": "The diff removes the automatic prune from invoke and renames the setting to warn_gb with no alias; it adds a shared size_warning helper used by doctor (as a WARN row, exit still 0) and by view status, adds the writer-locked `evidence prune --to-gb N` verb with full help, updates the fenced docs, and adds tests that cover every acceptance criterion.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
