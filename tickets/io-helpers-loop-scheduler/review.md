# Review: approve

The diff moves Rig, Time and text unchanged into tests/loop_helpers.py, re-exports turn from tests.fakes and adds scheduler_import_closure; it repoints all 16 importers and the regress script by import line only, leaves the hub importing the names back with only its now-unused imports removed, and adds unit tests for every moved name using tmp_path and in-memory inputs, all within the fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "63baba1f0286d9d242388a48d1d8c47558057cac",
  "stem": "io-helpers-loop-scheduler",
  "reviewed_sha": "63baba1f0286d9d242388a48d1d8c47558057cac",
  "summary": "The diff moves Rig, Time and text unchanged into tests/loop_helpers.py, re-exports turn from tests.fakes and adds scheduler_import_closure; it repoints all 16 importers and the regress script by import line only, leaves the hub importing the names back with only its now-unused imports removed, and adds unit tests for every moved name using tmp_path and in-memory inputs, all within the fence.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
