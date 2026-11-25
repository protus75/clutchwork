# Review: snag

The server tools and dashboard wiring are correct, but the tests the ticket requires leave several promised checks out, and a fractional Refresh seconds value drives polling but never gets saved.

## Findings

- [acceptance] tests/mcp_app_dashboard.js:49 Criteria 4, 5 and 7 say tests/integration/test_mcp_app_dashboard.py verifies them by running this harness, and Scope in lists the checks it must make. The harness only checks that the step-time span is the second child and that the last row has step-warning. It never checks step-passed on engine_start or *_ok rows, step-failed on engine_stop or *_failed rows, or step-muted on *_start rows. It never checks the engine_start/engine_stop outline paths or the preflight rocket path. It makes none of the dashboard.css checks: `.step-row:disabled { opacity: 1`, the four outcome color rules, no bold on .step-stem, no `margin-left: auto` on .step-time, and .step-text using descriptionForeground. It never checks that a section toggle, a resize pointerup or a drag-and-drop calls clutch_app_ui_state set; only the ▲ click is checked. On polling, it never checks that an overlapping refresh is skipped or that changing to a nonzero refreshSeconds resets the interval at the new period. So these criteria pass whether or not the behavior is there. (do instead: Add harness assertions: the class on each step row by kind (engine_start → step-passed, engine_stop → step-failed, *_start → step-muted); the icon paths; regexes over dashboard.css for each required CSS rule and for the absent bold and margin-left rules; a set call after a toggle dispatch, a resizer pointerup and a drop; and for polling, a nonzero change that clears the old interval and schedules one at the new ms, plus a second refresh during an in-flight one that makes no extra clutch_app_snapshot call.)
- [acceptance] tests/unit/test_mcp_ui_state_and_config.py:35 Criterion 2 and Definition of rejected require that clutch_app_config set keeps unrelated config.yaml keys. The test only checks the returned max_runs and never checks that other keys from VALID are still in the written file, so a set that drops keys would still pass. (do instead: After the successful set, load config.yaml with yaml.safe_load and assert that the top-level keys from VALID other than scheduler.parallel are still there with their original values.)
- [logic] clutch/ui/app.js:90 The Refresh seconds handler takes any non-negative number with `Math.max(0, Number(n.value) || 0)`, so 2.5 becomes the polling period. But clutch_app_ui_state merge only accepts an int refreshSeconds, so the server quietly keeps the old value. The dashboard then polls at a period that is never saved, and the preference is lost on reopen, which Definition of rejected forbids. (do instead: Round the client value to an integer (for example `Math.max(0, Math.round(Number(n.value)) || 0)`) and set `step = 1` on the number input, so the client and server accept the same values.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "f8a85a8516fa9448044d1f21fdea7a038a939a5b",
  "stem": "mcp-dashboard-settings-and-layout",
  "reviewed_sha": "f8a85a8516fa9448044d1f21fdea7a038a939a5b",
  "summary": "The server tools and dashboard wiring are correct, but the tests the ticket requires leave several promised checks out, and a fractional Refresh seconds value drives polling but never gets saved.",
  "findings": [
    {
      "code": "acceptance",
      "path": "tests/mcp_app_dashboard.js",
      "line": 49,
      "message": "Criteria 4, 5 and 7 say tests/integration/test_mcp_app_dashboard.py verifies them by running this harness, and Scope in lists the checks it must make. The harness only checks that the step-time span is the second child and that the last row has step-warning. It never checks step-passed on engine_start or *_ok rows, step-failed on engine_stop or *_failed rows, or step-muted on *_start rows. It never checks the engine_start/engine_stop outline paths or the preflight rocket path. It makes none of the dashboard.css checks: `.step-row:disabled { opacity: 1`, the four outcome color rules, no bold on .step-stem, no `margin-left: auto` on .step-time, and .step-text using descriptionForeground. It never checks that a section toggle, a resize pointerup or a drag-and-drop calls clutch_app_ui_state set; only the ▲ click is checked. On polling, it never checks that an overlapping refresh is skipped or that changing to a nonzero refreshSeconds resets the interval at the new period. So these criteria pass whether or not the behavior is there.",
      "paved_road": "Add harness assertions: the class on each step row by kind (engine_start → step-passed, engine_stop → step-failed, *_start → step-muted); the icon paths; regexes over dashboard.css for each required CSS rule and for the absent bold and margin-left rules; a set call after a toggle dispatch, a resizer pointerup and a drop; and for polling, a nonzero change that clears the old interval and schedules one at the new ms, plus a second refresh during an in-flight one that makes no extra clutch_app_snapshot call.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/unit/test_mcp_ui_state_and_config.py",
      "line": 35,
      "message": "Criterion 2 and Definition of rejected require that clutch_app_config set keeps unrelated config.yaml keys. The test only checks the returned max_runs and never checks that other keys from VALID are still in the written file, so a set that drops keys would still pass.",
      "paved_road": "After the successful set, load config.yaml with yaml.safe_load and assert that the top-level keys from VALID other than scheduler.parallel are still there with their original values.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "clutch/ui/app.js",
      "line": 90,
      "message": "The Refresh seconds handler takes any non-negative number with `Math.max(0, Number(n.value) || 0)`, so 2.5 becomes the polling period. But clutch_app_ui_state merge only accepts an int refreshSeconds, so the server quietly keeps the old value. The dashboard then polls at a period that is never saved, and the preference is lost on reopen, which Definition of rejected forbids.",
      "paved_road": "Round the client value to an integer (for example `Math.max(0, Math.round(Number(n.value)) || 0)`) and set `step = 1` on the number input, so the client and server accept the same values.",
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
