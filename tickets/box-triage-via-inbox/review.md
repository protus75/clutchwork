# Review: snag

The prior lifecycle-filter finding is fixed and the control, CLI, drain/serve and doc changes match the ticket, but acceptance criterion 8 has no test in the file that is supposed to check it.

## Findings

- [acceptance] tests/integration/test_box_triage_inbox.py:25 Acceptance criterion 8 says 'With the lock free, `clutch box triage` still runs a pass directly, as before', checked by `tests/integration/test_box_triage_inbox.py`. That file has only three tests: `test_prompt_bounds`, `test_submit_and_non_engine_refusal` and `test_serve_processes_only_requested_triage`. Every `main(["box", "triage", ...])` call in it runs while a `Lockfile` is held, so nothing covers the lock-free direct pass. The changed `try/except LockHeld` in `handle_triage` could break the direct path and the named check would still pass. (do instead: Add a test to `tests/integration/test_box_triage_inbox.py` that runs `main(["box", "triage", <id>], ...)` with no lock held and a fake provider reply (as `tests/integration/test_triage.py` does). Assert that it exits 0, prints the pass line rather than `triage submitted:`, gives the message a resolution, and leaves `control/inbox` with no request file.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "6a9ffe3cb17e5e00fcc7acba4a58d3a09c22ba93",
  "stem": "box-triage-via-inbox",
  "reviewed_sha": "6a9ffe3cb17e5e00fcc7acba4a58d3a09c22ba93",
  "summary": "The prior lifecycle-filter finding is fixed and the control, CLI, drain/serve and doc changes match the ticket, but acceptance criterion 8 has no test in the file that is supposed to check it.",
  "findings": [
    {
      "code": "acceptance",
      "path": "tests/integration/test_box_triage_inbox.py",
      "line": 25,
      "message": "Acceptance criterion 8 says 'With the lock free, `clutch box triage` still runs a pass directly, as before', checked by `tests/integration/test_box_triage_inbox.py`. That file has only three tests: `test_prompt_bounds`, `test_submit_and_non_engine_refusal` and `test_serve_processes_only_requested_triage`. Every `main([\"box\", \"triage\", ...])` call in it runs while a `Lockfile` is held, so nothing covers the lock-free direct pass. The changed `try/except LockHeld` in `handle_triage` could break the direct path and the named check would still pass.",
      "paved_road": "Add a test to `tests/integration/test_box_triage_inbox.py` that runs `main([\"box\", \"triage\", <id>], ...)` with no lock held and a fake provider reply (as `tests/integration/test_triage.py` does). Assert that it exits 0, prints the pass line rather than `triage submitted:`, gives the message a resolution, and leaves `control/inbox` with no request file.",
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
