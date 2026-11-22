# Review: snag

The move, the 20 import-line edits, the GitFake/FakeExec rewrites and the in-process notify-sink branch are correct, but tests/unit/test_loop_helpers.py leaves out the check criterion 1 requires: that serve_rig.until and serve_rig.turn still resolve.

## Findings

- [acceptance] tests/unit/test_loop_helpers.py:410 Acceptance criterion 1 requires tests/unit/test_loop_helpers.py to check that `serve_rig.until` and `serve_rig.turn` still resolve (`serve_rig.turn is tests.fakes.turn`). None of the added tests (test_serve_exports through test_serve_enable_upgrade) imports tests.integration.serve_rig or asserts on `until` or `turn`, so that part of the criterion is unmet. The hub could lose either attribute after this move and this test file would still pass. (do instead: Append a test to tests/unit/test_loop_helpers.py that runs `from tests.integration import serve_rig`, asserts `serve_rig.turn is fakes.turn` and `callable(serve_rig.until)`, and also asserts that each moved name on the hub (for example `serve_rig.graph is loop_helpers.graph`) is the shared object.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "63ac2ea4d0a5d5c3a11e81cfbfdb82dbffc68151",
  "stem": "io-helpers-loop-serve-rig",
  "reviewed_sha": "63ac2ea4d0a5d5c3a11e81cfbfdb82dbffc68151",
  "summary": "The move, the 20 import-line edits, the GitFake/FakeExec rewrites and the in-process notify-sink branch are correct, but tests/unit/test_loop_helpers.py leaves out the check criterion 1 requires: that serve_rig.until and serve_rig.turn still resolve.",
  "findings": [
    {
      "code": "acceptance",
      "path": "tests/unit/test_loop_helpers.py",
      "line": 410,
      "message": "Acceptance criterion 1 requires tests/unit/test_loop_helpers.py to check that `serve_rig.until` and `serve_rig.turn` still resolve (`serve_rig.turn is tests.fakes.turn`). None of the added tests (test_serve_exports through test_serve_enable_upgrade) imports tests.integration.serve_rig or asserts on `until` or `turn`, so that part of the criterion is unmet. The hub could lose either attribute after this move and this test file would still pass.",
      "paved_road": "Append a test to tests/unit/test_loop_helpers.py that runs `from tests.integration import serve_rig`, asserts `serve_rig.turn is fakes.turn` and `callable(serve_rig.until)`, and also asserts that each moved name on the hub (for example `serve_rig.graph is loop_helpers.graph`) is the shared object.",
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
