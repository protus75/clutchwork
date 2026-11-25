# Review: snag

The dashboard wires all six surfaces and the host adapter correctly, but Help & Lifecycle drops every help link that is file-based (`{label, path, line}`) instead of URL-based.

## Findings

- [logic] clutch/ui/app.js:93 The Help & Lifecycle tab sets `link.href = entry.link.url` for every `snap.help` entry. `clutch/help.py` `help_map` (lines 234 and 240) builds links for topics whose doc is a shipped guide (`host-running.md` verb rows, `host-contract.md` command entries) as `{label, path, line}` with no `url`. Those topics therefore render as anchors with an undefined href that do nothing when clicked. The ticket requires `snap.help` topics and links to work. (do instead: Render a path-based link as a button or anchor whose click handler calls `openFile(entry.link.path)`. Keep `href`/`target=_blank` only for entries that have `link.url`. Add a path-only help entry to `tests/mcp_app_dashboard.js` and assert that clicking it sends a `toggle-aux-pane` request.)
- [logic] clutch/ui/app.js:52 `host.openHelp` only handles `snap.help[topic].link.url`. When `detail.js` calls `host.openHelp(topic)` (line 40) for a topic whose link is path-based (shipped `host-*.md` guide), nothing happens and no notice is shown. That help link is dead in the Details view. (do instead: In `openHelp`, call `openFile(link.path)` when the link has `path` and no `url`. Fall back to `window.open(link.url)` only for URL links. Cover both cases in the Node harness.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "4010677b82195017cca7d36448e02daa6c63fb57",
  "stem": "mcp-dashboard-surfaces",
  "reviewed_sha": "4010677b82195017cca7d36448e02daa6c63fb57",
  "summary": "The dashboard wires all six surfaces and the host adapter correctly, but Help & Lifecycle drops every help link that is file-based (`{label, path, line}`) instead of URL-based.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/ui/app.js",
      "line": 93,
      "message": "The Help & Lifecycle tab sets `link.href = entry.link.url` for every `snap.help` entry. `clutch/help.py` `help_map` (lines 234 and 240) builds links for topics whose doc is a shipped guide (`host-running.md` verb rows, `host-contract.md` command entries) as `{label, path, line}` with no `url`. Those topics therefore render as anchors with an undefined href that do nothing when clicked. The ticket requires `snap.help` topics and links to work.",
      "paved_road": "Render a path-based link as a button or anchor whose click handler calls `openFile(entry.link.path)`. Keep `href`/`target=_blank` only for entries that have `link.url`. Add a path-only help entry to `tests/mcp_app_dashboard.js` and assert that clicking it sends a `toggle-aux-pane` request.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "clutch/ui/app.js",
      "line": 52,
      "message": "`host.openHelp` only handles `snap.help[topic].link.url`. When `detail.js` calls `host.openHelp(topic)` (line 40) for a topic whose link is path-based (shipped `host-*.md` guide), nothing happens and no notice is shown. That help link is dead in the Details view.",
      "paved_road": "In `openHelp`, call `openFile(link.path)` when the link has `path` and no `url`. Fall back to `window.open(link.url)` only for URL links. Cover both cases in the Node harness.",
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
