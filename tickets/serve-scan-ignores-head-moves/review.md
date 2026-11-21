# Review: snag

The serve.py change and the tests meet the criteria, but each of the three new test files has a stale second `clutch:meta` block left over from an earlier header that was never removed.

## Findings

- [acceptance] tests/unit/test_serve_scan_head.py:11 The file has two `# clutch:meta` blocks. `clutch/meta.py` `parse` reads only the first block, so the second block (lines 11-18) is part of the body: a stale header with its own unused purpose and a hash that matches nothing. Scope in asks for one header made by `clutch meta refresh`, with only the purpose line edited by hand. (do instead: Delete the second `# clutch:meta` block (lines 11-18) and its blank separator, keep the first block's purpose, then rerun `uv run clutch meta refresh tests/unit/test_serve_scan_head.py` so the hash matches the body.)
- [acceptance] tests/integration/test_serve_scan_head.py:11 The file has two `# clutch:meta` blocks. The second block (lines 11-18) is stale metadata that `parse` treats as body text: a duplicate header with a hash that matches nothing. Scope in asks for one header made by `clutch meta refresh`. (do instead: Delete the second `# clutch:meta` block (lines 11-18) and the blank line before it, then rerun `uv run clutch meta refresh tests/integration/test_serve_scan_head.py`.)
- [acceptance] tests/regress_serve_scan_head.py:11 The file has two `# clutch:meta` blocks. The second block (lines 11-18) is a stale header whose purpose differs from the first and whose hash matches nothing. `parse` reads only the first block, so the second is dead metadata in the body. Scope in asks for one header made by `clutch meta refresh`. (do instead: Delete the second `# clutch:meta` block (lines 11-18) and the blank line before it, then rerun `uv run clutch meta refresh tests/regress_serve_scan_head.py`.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "0414a3543b2f9c5cf8e4e0b944906e8405110355",
  "stem": "serve-scan-ignores-head-moves",
  "reviewed_sha": "0414a3543b2f9c5cf8e4e0b944906e8405110355",
  "summary": "The serve.py change and the tests meet the criteria, but each of the three new test files has a stale second `clutch:meta` block left over from an earlier header that was never removed.",
  "findings": [
    {
      "code": "acceptance",
      "path": "tests/unit/test_serve_scan_head.py",
      "line": 11,
      "message": "The file has two `# clutch:meta` blocks. `clutch/meta.py` `parse` reads only the first block, so the second block (lines 11-18) is part of the body: a stale header with its own unused purpose and a hash that matches nothing. Scope in asks for one header made by `clutch meta refresh`, with only the purpose line edited by hand.",
      "paved_road": "Delete the second `# clutch:meta` block (lines 11-18) and its blank separator, keep the first block's purpose, then rerun `uv run clutch meta refresh tests/unit/test_serve_scan_head.py` so the hash matches the body.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/integration/test_serve_scan_head.py",
      "line": 11,
      "message": "The file has two `# clutch:meta` blocks. The second block (lines 11-18) is stale metadata that `parse` treats as body text: a duplicate header with a hash that matches nothing. Scope in asks for one header made by `clutch meta refresh`.",
      "paved_road": "Delete the second `# clutch:meta` block (lines 11-18) and the blank line before it, then rerun `uv run clutch meta refresh tests/integration/test_serve_scan_head.py`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/regress_serve_scan_head.py",
      "line": 11,
      "message": "The file has two `# clutch:meta` blocks. The second block (lines 11-18) is a stale header whose purpose differs from the first and whose hash matches nothing. `parse` reads only the first block, so the second is dead metadata in the body. Scope in asks for one header made by `clutch meta refresh`.",
      "paved_road": "Delete the second `# clutch:meta` block (lines 11-18) and the blank line before it, then rerun `uv run clutch meta refresh tests/regress_serve_scan_head.py`.",
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
