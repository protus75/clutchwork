# Review: snag

The serve.py change and the tests meet criteria 1 to 6, but all three new files have an empty `purpose:` meta line, so `clutch meta check` reports `empty_purpose` and criterion 7 fails.

## Findings

- [acceptance] tests/unit/test_serve_scan_head.py:5 The clutch:meta `purpose:` line is empty. `clutch/meta.py` `check` reports `empty_purpose` for an empty purpose, so `uv run clutch meta check` on this file exits non-zero and criterion 7 fails. Scope in says the purpose line is the one line to edit by hand. (do instead: Write a one-line purpose, e.g. `purpose: Verify the intake snapshot ignores main moves unless a ticket file is pending.`, then rerun `uv run clutch meta refresh` on the file so the hash matches.)
- [acceptance] tests/integration/test_serve_scan_head.py:5 The clutch:meta `purpose:` line is empty, so `clutch meta check` reports `empty_purpose` for this file and criterion 7 fails. (do instead: Write a one-line purpose, e.g. `purpose: Verify main-only commits do not block parallel admission and refused tickets retry after a merge.`, then rerun `uv run clutch meta refresh`.)
- [acceptance] tests/regress_serve_scan_head.py:5 The clutch:meta `purpose:` line is empty, so `clutch meta check` reports `empty_purpose` for the regression reproducer and criterion 7 fails. (do instead: Write a one-line purpose, e.g. `purpose: Reproduce an intake snapshot changed by a main move with no pending ticket.`, then rerun `uv run clutch meta refresh`.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "a9ca54bc2d616335a0f1ed2230f56a81ccf16178",
  "stem": "serve-scan-ignores-head-moves",
  "reviewed_sha": "a9ca54bc2d616335a0f1ed2230f56a81ccf16178",
  "summary": "The serve.py change and the tests meet criteria 1 to 6, but all three new files have an empty `purpose:` meta line, so `clutch meta check` reports `empty_purpose` and criterion 7 fails.",
  "findings": [
    {
      "code": "acceptance",
      "path": "tests/unit/test_serve_scan_head.py",
      "line": 5,
      "message": "The clutch:meta `purpose:` line is empty. `clutch/meta.py` `check` reports `empty_purpose` for an empty purpose, so `uv run clutch meta check` on this file exits non-zero and criterion 7 fails. Scope in says the purpose line is the one line to edit by hand.",
      "paved_road": "Write a one-line purpose, e.g. `purpose: Verify the intake snapshot ignores main moves unless a ticket file is pending.`, then rerun `uv run clutch meta refresh` on the file so the hash matches.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/integration/test_serve_scan_head.py",
      "line": 5,
      "message": "The clutch:meta `purpose:` line is empty, so `clutch meta check` reports `empty_purpose` for this file and criterion 7 fails.",
      "paved_road": "Write a one-line purpose, e.g. `purpose: Verify main-only commits do not block parallel admission and refused tickets retry after a merge.`, then rerun `uv run clutch meta refresh`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/regress_serve_scan_head.py",
      "line": 5,
      "message": "The clutch:meta `purpose:` line is empty, so `clutch meta check` reports `empty_purpose` for the regression reproducer and criterion 7 fails.",
      "paved_road": "Write a one-line purpose, e.g. `purpose: Reproduce an intake snapshot changed by a main move with no pending ticket.`, then rerun `uv run clutch meta refresh`.",
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
