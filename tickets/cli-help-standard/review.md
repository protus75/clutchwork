# Review: approve

The diff meets every acceptance criterion and stays inside the fence: it adds the `_command` helper, makes `prompt` a group whose argv and refusals are unchanged, adds the `help` command and the `--help`/`-h <command>` forms without needing a config, replaces the flat command list with a grouped one, and adds the doc rows, the three repo-local rules and a structural test; the reads, writes, lock and exit facts in the help match `docs/how-clutch-works.md` section 2.1.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "54d690da628436c31f7fb48a478f001b65f99890",
  "stem": "cli-help-standard",
  "reviewed_sha": "54d690da628436c31f7fb48a478f001b65f99890",
  "summary": "The diff meets every acceptance criterion and stays inside the fence: it adds the `_command` helper, makes `prompt` a group whose argv and refusals are unchanged, adds the `help` command and the `--help`/`-h <command>` forms without needing a config, replaces the flat command list with a grouped one, and adds the doc rows, the three repo-local rules and a structural test; the reads, writes, lock and exit facts in the help match `docs/how-clutch-works.md` section 2.1.",
  "findings": [],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
