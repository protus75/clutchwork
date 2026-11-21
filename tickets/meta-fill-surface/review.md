# Review: snag

The owner-injection finding is fixed, but two defects remain: every non-ok driver outcome exits 2 as a 'provider failure', and the Python relates trim loop is copied in two places instead of living in one shared helper.

## Findings

- [logic] clutch/metafill.py:98 Every driver outcome other than ok is recorded with the reason `provider failure: <outcome>`. `_run_meta` (clutch/__main__.py:1106) then returns 2 for any reason with that prefix. So a batch the driver ended as `invalid_artifact` or `gate_failed` makes the command exit 2 as a provider failure. The ticket says a non-ok batch is rejected with its outcome as the reason, and that the command exits 1 when any file was rejected. Exit 2 is only for refusals: a malformed block, an over-bound render, or a provider failure. Both the reason text and the exit code are wrong for reply-validation outcomes. (do instead: Reject the batch's paths with the outcome itself as the reason. Return 2 only for outcomes that really are provider failures (for example infra_error). Return 1 for invalid_artifact or gate_failed. Add a case to tests/unit/test_main_meta_fill.py that pins exit 1 for a gate_failed outcome.)
- [acceptance] clutch/meta.py:137 The Python `# relates: [...]` 160-character trim loop appears twice: once in `generated` (here) and again in `compose` at line 153. Refresh trims through `generated`; fill trims through `compose(trim=True)`. The ticket asks for one shared helper that composes the block, including the trim, called by both refresh and fill. It also rejects a second code path for composing blocks, and two copies of the trim can drift apart. (do instead: Keep the trim in one place, for example only in `compose`, and pass `trim=True` from both `refresh` (when it generated relates) and `fill` (when it applied model relates). Remove the copy from `generated`. tests/unit/test_meta_refresh.py and the fill trim test must stay green.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "7b961cb95798a810cbb94e9499856e98a1209177",
  "stem": "meta-fill-surface",
  "reviewed_sha": "7b961cb95798a810cbb94e9499856e98a1209177",
  "summary": "The owner-injection finding is fixed, but two defects remain: every non-ok driver outcome exits 2 as a 'provider failure', and the Python relates trim loop is copied in two places instead of living in one shared helper.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/metafill.py",
      "line": 98,
      "message": "Every driver outcome other than ok is recorded with the reason `provider failure: <outcome>`. `_run_meta` (clutch/__main__.py:1106) then returns 2 for any reason with that prefix. So a batch the driver ended as `invalid_artifact` or `gate_failed` makes the command exit 2 as a provider failure. The ticket says a non-ok batch is rejected with its outcome as the reason, and that the command exits 1 when any file was rejected. Exit 2 is only for refusals: a malformed block, an over-bound render, or a provider failure. Both the reason text and the exit code are wrong for reply-validation outcomes.",
      "paved_road": "Reject the batch's paths with the outcome itself as the reason. Return 2 only for outcomes that really are provider failures (for example infra_error). Return 1 for invalid_artifact or gate_failed. Add a case to tests/unit/test_main_meta_fill.py that pins exit 1 for a gate_failed outcome.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "clutch/meta.py",
      "line": 137,
      "message": "The Python `# relates: [...]` 160-character trim loop appears twice: once in `generated` (here) and again in `compose` at line 153. Refresh trims through `generated`; fill trims through `compose(trim=True)`. The ticket asks for one shared helper that composes the block, including the trim, called by both refresh and fill. It also rejects a second code path for composing blocks, and two copies of the trim can drift apart.",
      "paved_road": "Keep the trim in one place, for example only in `compose`, and pass `trim=True` from both `refresh` (when it generated relates) and `fill` (when it applied model relates). Remove the copy from `generated`. tests/unit/test_meta_refresh.py and the fill trim test must stay green.",
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
