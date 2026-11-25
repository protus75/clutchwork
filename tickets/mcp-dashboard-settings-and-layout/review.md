# Review: snag

The prior dirty-input finding is fixed and the server tools, layout, steps styling and Settings wiring match the ticket, but the harness check that `refreshSeconds: 0` stops polling cannot fail.

## Findings

- [logic] tests/mcp_app_dashboard.js:51 After setting `Refresh seconds` to `0`, the test asserts `cleared.includes(1)`. Interval id 1 was already cleared by the earlier change to `2.5` (line 47), so this assertion passes even if `schedule()` neither clears the current interval (id 2) nor stops creating new ones. Nothing checks that no new interval is scheduled. Acceptance criterion 5 says polling is cleared when `refreshSeconds` is `0`, and this harness check cannot detect a regression there. (do instead: Before dispatching the `0` change, record `const live = intervals.length` (the active id). After the change, assert `cleared.includes(live)` and `intervals.length === live`, so the test fails unless the active timer is cleared and no replacement is scheduled.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "ac02407d7a6acb26595f301c3b72fd4ffc182bc5",
  "stem": "mcp-dashboard-settings-and-layout",
  "reviewed_sha": "ac02407d7a6acb26595f301c3b72fd4ffc182bc5",
  "summary": "The prior dirty-input finding is fixed and the server tools, layout, steps styling and Settings wiring match the ticket, but the harness check that `refreshSeconds: 0` stops polling cannot fail.",
  "findings": [
    {
      "code": "logic",
      "path": "tests/mcp_app_dashboard.js",
      "line": 51,
      "message": "After setting `Refresh seconds` to `0`, the test asserts `cleared.includes(1)`. Interval id 1 was already cleared by the earlier change to `2.5` (line 47), so this assertion passes even if `schedule()` neither clears the current interval (id 2) nor stops creating new ones. Nothing checks that no new interval is scheduled. Acceptance criterion 5 says polling is cleared when `refreshSeconds` is `0`, and this harness check cannot detect a regression there.",
      "paved_road": "Before dispatching the `0` change, record `const live = intervals.length` (the active id). After the change, assert `cleared.includes(live)` and `intervals.length === live`, so the test fails unless the active timer is cleared and no replacement is scheduled.",
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
