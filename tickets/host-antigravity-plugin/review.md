# Review: snag

The implementation meets the ticket, but the diff wrongly edits the `view status` row in host-running.md to say status warns about Antigravity plugin drift, and nothing in status does that.

## Findings

- [acceptance] clutch/docs/host-running.md:26 The diff changes the `view status` row to say "Warns when the installed Antigravity plugin MCP configuration drifts or its executable cannot resolve." `handle_status` in clutch/__main__.py never calls `antigravity.doctor_finding`. Only `doctor.check`, which `host doctor` runs, emits that warning, and the ticket asks only for the `host doctor` row to change. The run guide now gives operators wrong information about `view status`. (do instead: Restore the original `view status` row text and keep the Antigravity drift sentence only in the `host doctor` row.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "230908cbbc28bfc4d4010d1328b60b9498903af7",
  "stem": "host-antigravity-plugin",
  "reviewed_sha": "230908cbbc28bfc4d4010d1328b60b9498903af7",
  "summary": "The implementation meets the ticket, but the diff wrongly edits the `view status` row in host-running.md to say status warns about Antigravity plugin drift, and nothing in status does that.",
  "findings": [
    {
      "code": "acceptance",
      "path": "clutch/docs/host-running.md",
      "line": 26,
      "message": "The diff changes the `view status` row to say \"Warns when the installed Antigravity plugin MCP configuration drifts or its executable cannot resolve.\" `handle_status` in clutch/__main__.py never calls `antigravity.doctor_finding`. Only `doctor.check`, which `host doctor` runs, emits that warning, and the ticket asks only for the `host doctor` row to change. The run guide now gives operators wrong information about `view status`.",
      "paved_road": "Restore the original `view status` row text and keep the Antigravity drift sentence only in the `host doctor` row.",
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
