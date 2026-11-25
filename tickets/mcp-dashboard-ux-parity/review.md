# Review: snag

The server-side roots resolution, palette, context menu, header, hover/pin and boot-notice changes match the ticket, but dragging a section's summary can only drop it before the target, so a section cannot be dragged downward onto its next sibling or into the last position.

## Findings

- [logic] clutch/ui/app.js:77 The summary `drop` handler always calls `root.insertBefore(dragged, section)`. Dragging a section onto the section directly below it does nothing, any downward drag lands one slot short, and a section can never be dragged into the last position. The ticket's Scope in requires drop to reorder the dragged `.sidebar-section` "before or after the drop target section", and acceptance criterion 7 requires drag-and-drop reordering. The JS test only covers an upward drag. (do instead: In `drop`, insert after the target when the dragged section comes before it among `.sidebar-section` siblings (`root.insertBefore(dragged, section.nextSibling)`); otherwise insert before it. Add a `tests/mcp_app_dashboard.js` assertion that dragging a section onto the section below it moves it past that section.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "de4cfd9634e33ea4f43bfb6cd3659b338e80e825",
  "stem": "mcp-dashboard-ux-parity",
  "reviewed_sha": "de4cfd9634e33ea4f43bfb6cd3659b338e80e825",
  "summary": "The server-side roots resolution, palette, context menu, header, hover/pin and boot-notice changes match the ticket, but dragging a section's summary can only drop it before the target, so a section cannot be dragged downward onto its next sibling or into the last position.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/ui/app.js",
      "line": 77,
      "message": "The summary `drop` handler always calls `root.insertBefore(dragged, section)`. Dragging a section onto the section directly below it does nothing, any downward drag lands one slot short, and a section can never be dragged into the last position. The ticket's Scope in requires drop to reorder the dragged `.sidebar-section` \"before or after the drop target section\", and acceptance criterion 7 requires drag-and-drop reordering. The JS test only covers an upward drag.",
      "paved_road": "In `drop`, insert after the target when the dragged section comes before it among `.sidebar-section` siblings (`root.insertBefore(dragged, section.nextSibling)`); otherwise insert before it. Add a `tests/mcp_app_dashboard.js` assertion that dragging a section onto the section below it moves it past that section.",
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
