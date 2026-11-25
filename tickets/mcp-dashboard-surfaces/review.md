# Review: snag

The earlier help-link findings are fixed: path-based help links now open through openFile in both the Help tab and openHelp. The new engine play/stop controls are not gated by engine liveness, so criterion 1's admission-gated `clutch_engine_start` / `clutch_engine_control` requirement is unmet.

## Findings

- [acceptance] clutch/ui/app.js:89 `refresh` always shows the `Start drain` and `Start serve` buttons, even when it has just found the engine running (`ping.engine && snap.engine`). Criterion 1 requires `clutch_engine_start` calls to be admission-gated. The canonical surface gates them on liveness: `vscode-clutchwork/package.json` lines 561/566 show the play actions only when `!clutch.engineRunning`, set from `snap.engine` in `extension.js:122`. The app lets a second start fire against a running engine. The harness at `tests/mcp_app_dashboard.js:36` clicks `Start drain` while its fake ping returns `engine: true`, so it pins the ungated behavior. (do instead: Append the `Start drain` / `Start serve` buttons only when the computed liveness is false, reusing the same `ping.engine && snap.engine` value. In the harness, assert that the start buttons are absent while the engine is running, then make the fake ping/snapshot report the engine stopped, refresh, and click `Start drain`.)
- [acceptance] clutch/ui/app.js:90 `refresh` always shows the `Stop` button, even when liveness says the engine is stopped. Criterion 1 requires `clutch_engine_control` calls to be admission-gated. The canonical stop action is shown only when `clutch.engineRunning` is true (`vscode-clutchwork/package.json:571`). The harness never checks that `Stop` is hidden while the engine is stopped. (do instead: Append `Stop` only when the computed liveness is true. Add a harness assertion that `Stop` is absent after a refresh where the fake ping reports `engine: false`, and present and calling `clutch_engine_control` with `action: "stop"` when it reports `engine: true`.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "0bbe775b9d2bbc5cc680d378af2ad6ec30164c0f",
  "stem": "mcp-dashboard-surfaces",
  "reviewed_sha": "0bbe775b9d2bbc5cc680d378af2ad6ec30164c0f",
  "summary": "The earlier help-link findings are fixed: path-based help links now open through openFile in both the Help tab and openHelp. The new engine play/stop controls are not gated by engine liveness, so criterion 1's admission-gated `clutch_engine_start` / `clutch_engine_control` requirement is unmet.",
  "findings": [
    {
      "code": "acceptance",
      "path": "clutch/ui/app.js",
      "line": 89,
      "message": "`refresh` always shows the `Start drain` and `Start serve` buttons, even when it has just found the engine running (`ping.engine && snap.engine`). Criterion 1 requires `clutch_engine_start` calls to be admission-gated. The canonical surface gates them on liveness: `vscode-clutchwork/package.json` lines 561/566 show the play actions only when `!clutch.engineRunning`, set from `snap.engine` in `extension.js:122`. The app lets a second start fire against a running engine. The harness at `tests/mcp_app_dashboard.js:36` clicks `Start drain` while its fake ping returns `engine: true`, so it pins the ungated behavior.",
      "paved_road": "Append the `Start drain` / `Start serve` buttons only when the computed liveness is false, reusing the same `ping.engine && snap.engine` value. In the harness, assert that the start buttons are absent while the engine is running, then make the fake ping/snapshot report the engine stopped, refresh, and click `Start drain`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "clutch/ui/app.js",
      "line": 90,
      "message": "`refresh` always shows the `Stop` button, even when liveness says the engine is stopped. Criterion 1 requires `clutch_engine_control` calls to be admission-gated. The canonical stop action is shown only when `clutch.engineRunning` is true (`vscode-clutchwork/package.json:571`). The harness never checks that `Stop` is hidden while the engine is stopped.",
      "paved_road": "Append `Stop` only when the computed liveness is true. Add a harness assertion that `Stop` is absent after a refresh where the fake ping reports `engine: false`, and present and calling `clutch_engine_control` with `action: \"stop\"` when it reports `engine: true`.",
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
