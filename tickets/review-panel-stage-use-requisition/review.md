# Review: snag

The implementation follows the ticket and fixes both earlier test findings, but the criterion-6 test does not check two values the criterion names.

## Findings

- [acceptance] tests/unit/test_requisition_panel.py:202 Criterion 6 says the member-failing case has `member_count` 2 and `merged[0].members == [0]`, but `test_failures` checks neither. It checks `dropped`, `members[0].provider` and `merged[0].agreement`, and only checks that the combined verdict is `snag`, not that it equals member 1's. A regression in either value, such as one that reports `member_count` as the number of survivors or gives merged findings original member indexes, would still pass. (do instead: In the member-failing case, also assert `events[1]["member_count"] == 2` and `events[1]["merged"][0]["members"] == [0]`, and compare the returned verdict's `verdict`, `summary` and `findings` with member 1's reply (`snag`, `bad`, `[finding()]`).)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "92ffcc644d0b0bda79e95bc3f081dd329fa01c25",
  "stem": "review-panel-stage-use-requisition",
  "reviewed_sha": "92ffcc644d0b0bda79e95bc3f081dd329fa01c25",
  "summary": "The implementation follows the ticket and fixes both earlier test findings, but the criterion-6 test does not check two values the criterion names.",
  "findings": [
    {
      "code": "acceptance",
      "path": "tests/unit/test_requisition_panel.py",
      "line": 202,
      "message": "Criterion 6 says the member-failing case has `member_count` 2 and `merged[0].members == [0]`, but `test_failures` checks neither. It checks `dropped`, `members[0].provider` and `merged[0].agreement`, and only checks that the combined verdict is `snag`, not that it equals member 1's. A regression in either value, such as one that reports `member_count` as the number of survivors or gives merged findings original member indexes, would still pass.",
      "paved_road": "In the member-failing case, also assert `events[1][\"member_count\"] == 2` and `events[1][\"merged\"][0][\"members\"] == [0]`, and compare the returned verdict's `verdict`, `summary` and `findings` with member 1's reply (`snag`, `bad`, `[finding()]`).",
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
