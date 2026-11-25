# Review: snag

The earlier review findings are fixed, but box auto-open is now dead because the client treats the server's default open.box as a saved preference.

## Findings

- [logic] clutch/ui/app.js:203 The client sets `boxInitialized = typeof state.open?.box === "boolean"`. But clutch_app_ui_state get always merges the saved file over full defaults, and those defaults include `open.box: false`. So `open.box` is always a boolean and `boxInitialized` is always true. The existing auto-open in refresh (`sections.box.open = snap.boxCounts.pending > 0`) can then never run, even on a fresh install with no saved state. Scope in says to auto-open `box` whenever `open.box` was not saved. The harness hides this: its snapshot has pending=2, and it now asserts the box section is closed. (do instead: Let the client tell a saved open.box from the default. One way: the get reply also reports which `open` keys came from the file, such as a `saved` list or a flag for whether the file was read. Set `boxInitialized` only when `box` was actually saved. Add a harness case with no saved state and pending > 0 that asserts the Suggestion Box opens, plus one with saved `box: false` that asserts it stays closed.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "6f659b6bc5df6450ce3e05cf87fec87132a5778e",
  "stem": "mcp-dashboard-settings-and-layout",
  "reviewed_sha": "6f659b6bc5df6450ce3e05cf87fec87132a5778e",
  "summary": "The earlier review findings are fixed, but box auto-open is now dead because the client treats the server's default open.box as a saved preference.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/ui/app.js",
      "line": 203,
      "message": "The client sets `boxInitialized = typeof state.open?.box === \"boolean\"`. But clutch_app_ui_state get always merges the saved file over full defaults, and those defaults include `open.box: false`. So `open.box` is always a boolean and `boxInitialized` is always true. The existing auto-open in refresh (`sections.box.open = snap.boxCounts.pending > 0`) can then never run, even on a fresh install with no saved state. Scope in says to auto-open `box` whenever `open.box` was not saved. The harness hides this: its snapshot has pending=2, and it now asserts the box section is closed.",
      "paved_road": "Let the client tell a saved open.box from the default. One way: the get reply also reports which `open` keys came from the file, such as a `saved` list or a flag for whether the file was read. Set `boxInitialized` only when `box` was actually saved. Add a harness case with no saved state and pending > 0 that asserts the Suggestion Box opens, plus one with saved `box: false` that asserts it stays closed.",
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
