# Review: approve

The diff adds `prompts_dir`, moves the engine prompt descriptions and argument kinds into `ask.DESCRIPTIONS` and `ask.TAKES`, adds `ask.catalog` and `ask.render_host` that check host files and report bad ones as problems, and adds the `prompt host` and `prompt list` subcommands; existing prompt behavior is unchanged, the docs are updated, every acceptance criterion has a test, and every change is inside the scope fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "5f545bbf8198c2fd03b536c77673c55b0c671c52",
  "stem": "host-prompts",
  "reviewed_sha": "5f545bbf8198c2fd03b536c77673c55b0c671c52",
  "summary": "The diff adds `prompts_dir`, moves the engine prompt descriptions and argument kinds into `ask.DESCRIPTIONS` and `ask.TAKES`, adds `ask.catalog` and `ask.render_host` that check host files and report bad ones as problems, and adds the `prompt host` and `prompt list` subcommands; existing prompt behavior is unchanged, the docs are updated, every acceptance criterion has a test, and every change is inside the scope fence.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
