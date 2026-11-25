# Review: snag

The prior review's polling-test finding is fixed and the server tools, layout persistence, polling, labels, box parity, step styling and config dirty-tracking all match the ticket, but the new Settings `Stats window` select falls out of sync when the Stats section's own window select changes.

## Findings

- [logic] clutch/ui/app.js:73 The diff adds a second control for the same `statsWindow` value: `statsInput`, the Settings `Stats window` select. Its change handler copies its value into `windowSelect`, but the `windowSelect` change listener added on this line calls `persist()` and `loadStats()` without updating `statsInput.value`. If the operator picks `30d` in the Stats section, stats load and `30d` is persisted, but Settings still shows `7d` until the next reboot. The two UI-preference controls then disagree about the active window. (do instead: In the `windowSelect` change listener, also set `statsInput.value = windowSelect.value` (declare `statsInput` before use or assign it lazily) so both controls always show the persisted `statsWindow`. Add a harness assertion that changing the Stats section select updates the Settings `Stats window` value.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "c19ab7f5c36992ee3b34f0ce90c0f579fb0cad37",
  "stem": "mcp-dashboard-settings-and-layout",
  "reviewed_sha": "c19ab7f5c36992ee3b34f0ce90c0f579fb0cad37",
  "summary": "The prior review's polling-test finding is fixed and the server tools, layout persistence, polling, labels, box parity, step styling and config dirty-tracking all match the ticket, but the new Settings `Stats window` select falls out of sync when the Stats section's own window select changes.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/ui/app.js",
      "line": 73,
      "message": "The diff adds a second control for the same `statsWindow` value: `statsInput`, the Settings `Stats window` select. Its change handler copies its value into `windowSelect`, but the `windowSelect` change listener added on this line calls `persist()` and `loadStats()` without updating `statsInput.value`. If the operator picks `30d` in the Stats section, stats load and `30d` is persisted, but Settings still shows `7d` until the next reboot. The two UI-preference controls then disagree about the active window.",
      "paved_road": "In the `windowSelect` change listener, also set `statsInput.value = windowSelect.value` (declare `statsInput` before use or assign it lazily) so both controls always show the persisted `statsWindow`. Add a harness assertion that changing the Stats section select updates the Settings `Stats window` value.",
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
