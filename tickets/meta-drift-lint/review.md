# Review: approve

The diff adds `meta_drift` as a soft-by-default engine code, adds `MetaDriftGate` and `CHECK_ONLY_GATES`, and adds `check_meta`, which skips meta work on an empty changed-file list, maps reasons first-match, commits only the paths `meta.refresh` rewrote, and is wired after autofix and before candidates; it updates the pinned tests, fake configs and `docs/how-clutch-works.md` as the ticket asks, and leaves `clutch/meta.py` and every other out-of-fence file unchanged.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "da1e91f7d84222105bc0235bf07f96e771de8d62",
  "stem": "meta-drift-lint",
  "reviewed_sha": "da1e91f7d84222105bc0235bf07f96e771de8d62",
  "summary": "The diff adds `meta_drift` as a soft-by-default engine code, adds `MetaDriftGate` and `CHECK_ONLY_GATES`, and adds `check_meta`, which skips meta work on an empty changed-file list, maps reasons first-match, commits only the paths `meta.refresh` rewrote, and is wired after autofix and before candidates; it updates the pinned tests, fake configs and `docs/how-clutch-works.md` as the ticket asks, and leaves `clutch/meta.py` and every other out-of-fence file unchanged.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
