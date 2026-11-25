# Review: snag

The cursor, wait_once, CLI, docs and tests match the ticket, but the new CLI test file's meta header does not name the owner that Scope in requires.

## Findings

- [acceptance] tests/unit/test_main_view_events_once.py:6 Scope in requires `tests/unit/test_main_view_events_once.py` to have a `# clutch:meta` header with `owner: clutch/__main__.py`. The diff writes `# owner: engine`. (do instead: Change the header line to `# owner: clutch/__main__.py` and refresh the meta `verified`/`hash` fields so `uv run clutch meta check tests/unit/test_main_view_events_once.py` still passes.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "c5fdd91007ff4f775f7a8ba87466162c71df05b2",
  "stem": "events-once-cursor",
  "reviewed_sha": "c5fdd91007ff4f775f7a8ba87466162c71df05b2",
  "summary": "The cursor, wait_once, CLI, docs and tests match the ticket, but the new CLI test file's meta header does not name the owner that Scope in requires.",
  "findings": [
    {
      "code": "acceptance",
      "path": "tests/unit/test_main_view_events_once.py",
      "line": 6,
      "message": "Scope in requires `tests/unit/test_main_view_events_once.py` to have a `# clutch:meta` header with `owner: clutch/__main__.py`. The diff writes `# owner: engine`.",
      "paved_road": "Change the header line to `# owner: clutch/__main__.py` and refresh the meta `verified`/`hash` fields so `uv run clutch meta check tests/unit/test_main_view_events_once.py` still passes.",
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
