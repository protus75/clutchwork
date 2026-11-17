# Review: approve

The diff adds `clutch/calibration.py` with the named API, the `calibration.every` config key, the `engine calibrate` subcommand and handler (no lock taken, journals before printing, reuses `clutch.stats._summary`), the required doc rows, and tests that pin criteria 1-5, all within the scope fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "e6b33b18082e653aafdcb804ed30efaaa6521486",
  "stem": "estimate-calibration",
  "reviewed_sha": "e6b33b18082e653aafdcb804ed30efaaa6521486",
  "summary": "The diff adds `clutch/calibration.py` with the named API, the `calibration.every` config key, the `engine calibrate` subcommand and handler (no lock taken, journals before printing, reuses `clutch.stats._summary`), the required doc rows, and tests that pin criteria 1-5, all within the scope fence.",
  "findings": [],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
