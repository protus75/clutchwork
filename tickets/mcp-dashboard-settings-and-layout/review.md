# Review: snag

The earlier box auto-open finding is fixed (`savedOpen` is now honoured and both the fresh and the saved-closed cases are tested), but the new 15-second polling overwrites unsaved edits in the Settings config inputs, so Save config.yaml can send stale values.

## Findings

- [logic] clutch/ui/app.js:185 Every `refresh()` reloads `clutch_app_config` get and writes the result into every config input. This diff also makes `refresh()` run every `refreshSeconds` (default 15) and on window focus. So if an operator changes a value such as `Parallel max runs` and does not click Save within one poll, the input is reset to the on-disk value. Save config.yaml then sends the old value and the edit is silently lost. (do instead: Only fill the config inputs when the operator has nothing unsaved. For example, mark an input dirty on its `input`/`change` event, skip dirty inputs (or skip filling entirely) during `refresh()`, and clear the dirty flags after Save config.yaml succeeds. Add a harness case: edit an input, fire the interval callback, then assert the edited value survives and is what Save sends.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "fda1aedddc96016667722bd172e72575ad3d548f",
  "stem": "mcp-dashboard-settings-and-layout",
  "reviewed_sha": "fda1aedddc96016667722bd172e72575ad3d548f",
  "summary": "The earlier box auto-open finding is fixed (`savedOpen` is now honoured and both the fresh and the saved-closed cases are tested), but the new 15-second polling overwrites unsaved edits in the Settings config inputs, so Save config.yaml can send stale values.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/ui/app.js",
      "line": 185,
      "message": "Every `refresh()` reloads `clutch_app_config` get and writes the result into every config input. This diff also makes `refresh()` run every `refreshSeconds` (default 15) and on window focus. So if an operator changes a value such as `Parallel max runs` and does not click Save within one poll, the input is reset to the on-disk value. Save config.yaml then sends the old value and the edit is silently lost.",
      "paved_road": "Only fill the config inputs when the operator has nothing unsaved. For example, mark an input dirty on its `input`/`change` event, skip dirty inputs (or skip filling entirely) during `refresh()`, and clear the dirty flags after Save config.yaml succeeds. Add a harness case: edit an input, fire the interval callback, then assert the edited value survives and is what Save sends.",
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
