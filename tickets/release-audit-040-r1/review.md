# Review: snag

All three prior findings are fixed, the new row 155, the gate prose and the gate block are correct, but the rewritten §2.1 item 13 drops two fence-matching copies that are still in merge.py at the base commit.

## Findings

- [acceptance] docs/roadmap.md:55 §2.1 item 13 was rewritten to say only `watchdog.py` and `drain.py` still match paths on their own. At the base commit, `clutch/merge.py:102` and `clutch/merge.py:238` still use raw `startswith(f"{TICKETS_DIR}/")` instead of `tickets.in_fence`. No merged change fixed these two, so the rewrite drops part of the item that is still true. Criterion 3 forbids that. (do instead: Restore the merge.py copies in item 13 with their base-commit locations (`merge.py:102,238`), next to `watchdog.py:57` and `drain.py:562`. Keep the owner `tickets.in_fence` and the "(recurred in 0.4.0)" mark. Drop only the `stages.py` copy, which now calls `in_fence`.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "dbd7ab3ff6095c46fdc03ab3fc58ecc11e529a00",
  "stem": "release-audit-040-r1",
  "reviewed_sha": "dbd7ab3ff6095c46fdc03ab3fc58ecc11e529a00",
  "summary": "All three prior findings are fixed, the new row 155, the gate prose and the gate block are correct, but the rewritten §2.1 item 13 drops two fence-matching copies that are still in merge.py at the base commit.",
  "findings": [
    {
      "code": "acceptance",
      "path": "docs/roadmap.md",
      "line": 55,
      "message": "§2.1 item 13 was rewritten to say only `watchdog.py` and `drain.py` still match paths on their own. At the base commit, `clutch/merge.py:102` and `clutch/merge.py:238` still use raw `startswith(f\"{TICKETS_DIR}/\")` instead of `tickets.in_fence`. No merged change fixed these two, so the rewrite drops part of the item that is still true. Criterion 3 forbids that.",
      "paved_road": "Restore the merge.py copies in item 13 with their base-commit locations (`merge.py:102,238`), next to `watchdog.py:57` and `drain.py:562`. Keep the owner `tickets.in_fence` and the \"(recurred in 0.4.0)\" mark. Drop only the `stages.py` copy, which now calls `in_fence`.",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.7",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
