# Review: approve

The diff adds `read_bytes` and `size` to the `FileSystem` protocol and `LocalFileSystem`, adds raising stubs to `FakeFS` (the only change in that file), and adds four `tmp_path`-only tests that fail on a wrong implementation; it meets all five acceptance criteria and stays inside the scope fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "78815d6565deb99bd08534d6b1aa2db279caa171",
  "stem": "fs-seam-read-size",
  "reviewed_sha": "78815d6565deb99bd08534d6b1aa2db279caa171",
  "summary": "The diff adds `read_bytes` and `size` to the `FileSystem` protocol and `LocalFileSystem`, adds raising stubs to `FakeFS` (the only change in that file), and adds four `tmp_path`-only tests that fail on a wrong implementation; it meets all five acceptance criteria and stays inside the scope fence.",
  "findings": [],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
