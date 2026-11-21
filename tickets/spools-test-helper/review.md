# Review: snag

The helper, the reroutes and the tests meet the criteria, but both new files have a clutch:meta header that `clutch/meta.py::parse` rejects as malformed because the `verified` and `hash` keys are missing.

## Findings

- [acceptance] tests/spool_captures.py:6 The clutch:meta block has only six lines (schema, kind, purpose, relates, owner), followed by a blank line. `clutch/meta.py::parse` needs exactly the seven KEYS (schema, kind, purpose, relates, owner, verified, hash) on the seven lines after `# clutch:meta`, each starting with `# `. It raises Malformed here, so the meta refresh skips this file and reports it as `malformed`. The Scope in asks for a valid header with a purpose that the meta refresh renders. (do instead: Add `# verified:` and `# hash:` lines after `# owner: engine`, or run `uv run clutch meta fill tests/spool_captures.py` so the meta refresh writes them.)
- [acceptance] tests/unit/test_spool_captures.py:6 Same defect: the clutch:meta block has no `verified` or `hash` key, so `clutch/meta.py::parse` raises Malformed and the meta refresh reports the file as `malformed` instead of keeping its purpose. (do instead: Add `# verified:` and `# hash:` lines after `# owner: engine`, or run `uv run clutch meta fill tests/unit/test_spool_captures.py`.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "77e12d234147eb09fb33a9e0d7384e8fbbaa4df4",
  "stem": "spools-test-helper",
  "reviewed_sha": "77e12d234147eb09fb33a9e0d7384e8fbbaa4df4",
  "summary": "The helper, the reroutes and the tests meet the criteria, but both new files have a clutch:meta header that `clutch/meta.py::parse` rejects as malformed because the `verified` and `hash` keys are missing.",
  "findings": [
    {
      "code": "acceptance",
      "path": "tests/spool_captures.py",
      "line": 6,
      "message": "The clutch:meta block has only six lines (schema, kind, purpose, relates, owner), followed by a blank line. `clutch/meta.py::parse` needs exactly the seven KEYS (schema, kind, purpose, relates, owner, verified, hash) on the seven lines after `# clutch:meta`, each starting with `# `. It raises Malformed here, so the meta refresh skips this file and reports it as `malformed`. The Scope in asks for a valid header with a purpose that the meta refresh renders.",
      "paved_road": "Add `# verified:` and `# hash:` lines after `# owner: engine`, or run `uv run clutch meta fill tests/spool_captures.py` so the meta refresh writes them.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/unit/test_spool_captures.py",
      "line": 6,
      "message": "Same defect: the clutch:meta block has no `verified` or `hash` key, so `clutch/meta.py::parse` raises Malformed and the meta refresh reports the file as `malformed` instead of keeping its purpose.",
      "paved_road": "Add `# verified:` and `# hash:` lines after `# owner: engine`, or run `uv run clutch meta fill tests/unit/test_spool_captures.py`.",
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
