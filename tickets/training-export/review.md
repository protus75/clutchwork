# Review: snag

The export core, store listing, git trailer listing, CLI group and doc rows match the ticket, but the manifest error path over-counts skipped records for the preference kind.

## Findings

- [logic] clutch/training.py:141 When a manifest's call, blob or diff is missing, `counts["skipped"] += len(records)` counts one skip for every requested kind. That includes `preference` even when no preference record could be built for the stem: the stem has no merged commit, or the manifest is not `negative`. The ticket counts a kind as skipped only when that kind 'cannot be built for a stem because its implement call, blob or diff is missing', so the printed skipped count is too high. `tests/unit/test_training_export.py::test_missing_and_skipped` locks in this wrong count with `counts["skipped"] == 3`, even though stem `b` has no merged commit and could never yield a preference record. (do instead: In the attempts-loop `except`, count `implement` when it was requested. Count `preference` only when it was requested and the stem is in `merged`; or, if the labels can be read, only when the manifest's findings make it `negative`. Then change the test to expect the correct count (2 in that fixture).)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "0e8c00a59ad362eea45c233aad06960698401743",
  "stem": "training-export",
  "reviewed_sha": "0e8c00a59ad362eea45c233aad06960698401743",
  "summary": "The export core, store listing, git trailer listing, CLI group and doc rows match the ticket, but the manifest error path over-counts skipped records for the preference kind.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/training.py",
      "line": 141,
      "message": "When a manifest's call, blob or diff is missing, `counts[\"skipped\"] += len(records)` counts one skip for every requested kind. That includes `preference` even when no preference record could be built for the stem: the stem has no merged commit, or the manifest is not `negative`. The ticket counts a kind as skipped only when that kind 'cannot be built for a stem because its implement call, blob or diff is missing', so the printed skipped count is too high. `tests/unit/test_training_export.py::test_missing_and_skipped` locks in this wrong count with `counts[\"skipped\"] == 3`, even though stem `b` has no merged commit and could never yield a preference record.",
      "paved_road": "In the attempts-loop `except`, count `implement` when it was requested. Count `preference` only when it was requested and the stem is in `merged`; or, if the labels can be read, only when the manifest's findings make it `negative`. Then change the test to expect the correct count (2 in that fixture).",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
