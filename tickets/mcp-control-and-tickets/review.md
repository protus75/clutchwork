# Review: rma

The refactor moves `_require_engine` and the `control.read_active` / `control.publish_request` calls out of `clutch/__main__.py`, which breaks the out-of-fence call-ownership test `tests/integration/test_main_verb_groups.py`; that test can only be fixed outside `## Scope fence`, and there are in-fence defects as well.

## Findings

- [ticket] clutch/__main__.py:2135 `tests/integration/test_main_verb_groups.py::test_shared_call_has_one_owner` asserts three call sites with `ast` checks. It expects `_require_engine(...)`, `control.read_active(...)` and `control.publish_request(...)` to each be called exactly once, inside `_submit_engine`. The diff deletes `_require_engine` and moves its check into `runner.submit_engine`. It also passes `control.read_active` and `control.publish_request` as keyword values, which are not Call nodes, so all three parametrizations now get `[]` instead of `['_submit_engine']`. The ticket requires this move into `clutch/runner.py`, but that test file is not in `## Scope fence`. (do instead: Add `tests/integration/test_main_verb_groups.py` to `## Scope fence` and `## Context`. Allow its owner table to change so it pins the moved calls to `runner.submit_engine` in `clutch/runner.py`. Then re-run Implement.)
- [ticket] clutch/runner.py:1004 The new `runner.locked` copies `clutch/__main__.py::_locked` line for line (Lockfile acquire, yield, release in finally). That creates a second owner for the writer-lock context, and no boundary in the ticket declares it. `mcp.py` uses `runner.locked` while the CLI uses `_locked`. (do instead: Declare one canonical lock-context owner: move `_locked` into `clutch/runner.py`, have `clutch/__main__.py` import or alias it, and use it from both the CLI and MCP. Do not keep two copies.)
- [ticket] clutch/docs/host-running.md:- The `mcp serve` row changes column 2 ('Works while serve runs?') from `Yes` to `no (tools acquire their domain locks)`. That is wrong: the MCP server keeps running while serve runs. Its read tools work, and its mutation tools submit to the running engine's inbox when they hit `LockHeld`. (do instead: Keep `Yes` in the 'Works while serve runs?' column. Say in the description that mutation tools submit to the running engine's inbox.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "c73ee052bb458592ee656c2aef50c74b239822b5",
  "stem": "mcp-control-and-tickets",
  "reviewed_sha": "c73ee052bb458592ee656c2aef50c74b239822b5",
  "summary": "The refactor moves `_require_engine` and the `control.read_active` / `control.publish_request` calls out of `clutch/__main__.py`, which breaks the out-of-fence call-ownership test `tests/integration/test_main_verb_groups.py`; that test can only be fixed outside `## Scope fence`, and there are in-fence defects as well.",
  "findings": [
    {
      "code": "ticket",
      "path": "clutch/__main__.py",
      "line": 2135,
      "message": "`tests/integration/test_main_verb_groups.py::test_shared_call_has_one_owner` asserts three call sites with `ast` checks. It expects `_require_engine(...)`, `control.read_active(...)` and `control.publish_request(...)` to each be called exactly once, inside `_submit_engine`. The diff deletes `_require_engine` and moves its check into `runner.submit_engine`. It also passes `control.read_active` and `control.publish_request` as keyword values, which are not Call nodes, so all three parametrizations now get `[]` instead of `['_submit_engine']`. The ticket requires this move into `clutch/runner.py`, but that test file is not in `## Scope fence`.",
      "paved_road": "Add `tests/integration/test_main_verb_groups.py` to `## Scope fence` and `## Context`. Allow its owner table to change so it pins the moved calls to `runner.submit_engine` in `clutch/runner.py`. Then re-run Implement.",
      "kind": null,
      "unit": null
    },
    {
      "code": "ticket",
      "path": "clutch/runner.py",
      "line": 1004,
      "message": "The new `runner.locked` copies `clutch/__main__.py::_locked` line for line (Lockfile acquire, yield, release in finally). That creates a second owner for the writer-lock context, and no boundary in the ticket declares it. `mcp.py` uses `runner.locked` while the CLI uses `_locked`.",
      "paved_road": "Declare one canonical lock-context owner: move `_locked` into `clutch/runner.py`, have `clutch/__main__.py` import or alias it, and use it from both the CLI and MCP. Do not keep two copies.",
      "kind": null,
      "unit": null
    },
    {
      "code": "ticket",
      "path": "clutch/docs/host-running.md",
      "line": null,
      "message": "The `mcp serve` row changes column 2 ('Works while serve runs?') from `Yes` to `no (tools acquire their domain locks)`. That is wrong: the MCP server keeps running while serve runs. Its read tools work, and its mutation tools submit to the running engine's inbox when they hit `LockHeld`.",
      "paved_road": "Keep `Yes` in the 'Works while serve runs?' column. Say in the description that mutation tools submit to the running engine's inbox.",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "rma"
}
```
