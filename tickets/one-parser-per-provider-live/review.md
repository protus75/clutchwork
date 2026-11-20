# Review: approve

The diff makes `live_call` read the newest open `start.json` under `state/evidence/calls` (matched on stem prefix, surface and `began`, skipping any call with `end.json`), wires it into `text_snapshot`, meets every acceptance criterion with tests in `tmp_path`, and stays inside the fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "2c42e3c7de81afade3b8d1e87b5feeff40d42904",
  "stem": "one-parser-per-provider-live",
  "reviewed_sha": "2c42e3c7de81afade3b8d1e87b5feeff40d42904",
  "summary": "The diff makes `live_call` read the newest open `start.json` under `state/evidence/calls` (matched on stem prefix, surface and `began`, skipping any call with `end.json`), wires it into `text_snapshot`, meets every acceptance criterion with tests in `tmp_path`, and stays inside the fence.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
