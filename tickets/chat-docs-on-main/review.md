# Review: approve

The diff adds exception (6) with the required exclusions, adds a `Commit only when asked` clause, and extends the `Why:` with one clause, all in `CORE_TEMPLATE`; it shortens other rules without dropping or weakening any of them, keeps the three managed blocks byte-identical to the template, regenerates `GOLDEN` (the only other changes in that file are the metafill-maintained `verified`/`hash` header lines), and adds a disk-free unit test that fails if the exception or its exclusions are removed.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "0bbffffdc8b1fb2fbd7878c19eea4da763e0d58c",
  "stem": "chat-docs-on-main",
  "reviewed_sha": "0bbffffdc8b1fb2fbd7878c19eea4da763e0d58c",
  "summary": "The diff adds exception (6) with the required exclusions, adds a `Commit only when asked` clause, and extends the `Why:` with one clause, all in `CORE_TEMPLATE`; it shortens other rules without dropping or weakening any of them, keeps the three managed blocks byte-identical to the template, regenerates `GOLDEN` (the only other changes in that file are the metafill-maintained `verified`/`hash` header lines), and adds a disk-free unit test that fails if the exception or its exclusions are removed.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
