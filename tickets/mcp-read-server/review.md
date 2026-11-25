# Review: snag

The server, shared helpers and tests mostly match the ticket, but the README edit breaks the Observing code block and clutch_stats reports any ValueError as an invalid window.

## Findings

- [acceptance] README.md:85 The new lines add a second ```sh fence inside the existing ```sh block under `# Observing`. The inner opening line is read as content and its closing fence ends the outer block. So `uv run clutch view status`, `view watch`, `view stats`, `view events`, and the `# Decisions` commands now render as prose, and the old closing ``` opens a stray code block that runs into `## VS Code extension`. (do instead: Remove the added inner fence lines and put `uv run clutch mcp serve  # run the stdio MCP server` as a plain line inside the existing ```sh block under `# Observing`.)
- [logic] clutch/mcp.py:159 `clutch_stats` wraps all of `stats.collect_stats(...)` in `except ValueError` and maps it to `code="invalid_window"` with the road `use <N>h, <N>d, or <N>t`. `collect_stats` also raises ValueError subclasses that have nothing to do with the window, for example a pydantic `ValidationError` from `Invoice.model_validate_json` on a corrupt `checks.json`. Those get reported as a bad window, with a paved road that cannot fix them. The ticket asks for `stats.window_start` + `stats.collect_stats`, mapping only a bad window to `invalid_window`. (do instead: Call `stats.window_start(events, now, args.window)` first, inside the `except ValueError` that maps to `invalid_window` (as `handle_stats` does). Then call `collect_stats` outside that handler so other failures reach the general error mapping.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "47c9d060ca9e9bf7730d90b0e89689b8c93c11d7",
  "stem": "mcp-read-server",
  "reviewed_sha": "47c9d060ca9e9bf7730d90b0e89689b8c93c11d7",
  "summary": "The server, shared helpers and tests mostly match the ticket, but the README edit breaks the Observing code block and clutch_stats reports any ValueError as an invalid window.",
  "findings": [
    {
      "code": "acceptance",
      "path": "README.md",
      "line": 85,
      "message": "The new lines add a second ```sh fence inside the existing ```sh block under `# Observing`. The inner opening line is read as content and its closing fence ends the outer block. So `uv run clutch view status`, `view watch`, `view stats`, `view events`, and the `# Decisions` commands now render as prose, and the old closing ``` opens a stray code block that runs into `## VS Code extension`.",
      "paved_road": "Remove the added inner fence lines and put `uv run clutch mcp serve  # run the stdio MCP server` as a plain line inside the existing ```sh block under `# Observing`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "clutch/mcp.py",
      "line": 159,
      "message": "`clutch_stats` wraps all of `stats.collect_stats(...)` in `except ValueError` and maps it to `code=\"invalid_window\"` with the road `use <N>h, <N>d, or <N>t`. `collect_stats` also raises ValueError subclasses that have nothing to do with the window, for example a pydantic `ValidationError` from `Invoice.model_validate_json` on a corrupt `checks.json`. Those get reported as a bad window, with a paved road that cannot fix them. The ticket asks for `stats.window_start` + `stats.collect_stats`, mapping only a bad window to `invalid_window`.",
      "paved_road": "Call `stats.window_start(events, now, args.window)` first, inside the `except ValueError` that maps to `invalid_window` (as `handle_stats` does). Then call `collect_stats` outside that handler so other failures reach the general error mapping.",
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
