# Review: approve

The diff removes all 25 engine pass-throughs, the `clutch()` helper and the fallback from `dev.py` without changing `test`, `publish`, `vscode`, `vscode-package` or the bare suite run; it rewrites the rule, guide, README and doc mentions as the ticket asks, keeps CLAUDE.md and AGENTS.md identical, removes the `clutch/docs/` prune and asserts that directory is scanned, and adds tests that reject engine verbs as `dev.py` subcommands and check that a surviving subcommand rejects an unknown option.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "e42037c909d12dfd258f35df7e39a50eb53e3ba9",
  "stem": "dev-py-dev-tasks-only",
  "reviewed_sha": "e42037c909d12dfd258f35df7e39a50eb53e3ba9",
  "summary": "The diff removes all 25 engine pass-throughs, the `clutch()` helper and the fallback from `dev.py` without changing `test`, `publish`, `vscode`, `vscode-package` or the bare suite run; it rewrites the rule, guide, README and doc mentions as the ticket asks, keeps CLAUDE.md and AGENTS.md identical, removes the `clutch/docs/` prune and asserts that directory is scanned, and adds tests that reject engine verbs as `dev.py` subcommands and check that a surviving subcommand rejects an unknown option.",
  "findings": [],
  "spec_version": "1.5",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
