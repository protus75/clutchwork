# Review: approve

The diff adds only the three fenced files: the fakes match the `clutch.seams` and `clutch.journal` signatures, `turn` is an exact copy of `test_scheduler.py::turn`, `until` advances the clock on turns 0, 20 and 40 just as `serve_rig.until` does, and each acceptance criterion has a test in `tests/unit/test_shared_fakes.py` that can fail.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "4fc91fd01dbc4eeefff90c6179812cce14645654",
  "stem": "shared-test-fakes",
  "reviewed_sha": "4fc91fd01dbc4eeefff90c6179812cce14645654",
  "summary": "The diff adds only the three fenced files: the fakes match the `clutch.seams` and `clutch.journal` signatures, `turn` is an exact copy of `test_scheduler.py::turn`, `until` advances the clock on turns 0, 20 and 40 just as `serve_rig.until` does, and each acceptance criterion has a test in `tests/unit/test_shared_fakes.py` that can fail.",
  "findings": [],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
