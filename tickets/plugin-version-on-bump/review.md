# Review: approve

The diff meets every acceptance criterion: when the ClutchWork bundle is present, release() finds it through fs.read_bytes, refuses dirty bundle files before uv runs or anything is written, regenerates the files from portable_bundle_files at the bumped version and commits them with the three base files; non-bundle repos keep the same 3-file path and refusal text, the new tests use only fakes, and the help and both docs are updated within the fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "bf529793861904628af499eee21b0405c0598fb6",
  "stem": "plugin-version-on-bump",
  "reviewed_sha": "bf529793861904628af499eee21b0405c0598fb6",
  "summary": "The diff meets every acceptance criterion: when the ClutchWork bundle is present, release() finds it through fs.read_bytes, refuses dirty bundle files before uv runs or anything is written, regenerates the files from portable_bundle_files at the bumped version and commits them with the three base files; non-bundle repos keep the same 3-file path and refusal text, the new tests use only fakes, and the help and both docs are updated within the fence.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
