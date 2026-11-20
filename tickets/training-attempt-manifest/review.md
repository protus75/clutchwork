# Review: snag

The manifest model, store reader and writer, harvest hook, docs and tests meet the criteria, but git-quoted non-ASCII paths are decoded into mojibake, so a user exclude glob with non-ASCII characters can fail to match and the file's content gets stored.

## Findings

- [leak] clutch/runner.py:579 By default git C-quotes non-ASCII path bytes as octal escapes (core.quotePath=true), for example "a/secr\303\251t.key". `ast.literal_eval` turns each escape into a Latin-1 code point, giving 'a/secrÃ©t.key' instead of the UTF-8 path 'a/secrét.key'. The ASCII default globs still match. A configured `training_data.exclude` pattern containing non-ASCII characters (for example 'secrét*') never matches the decoded path, so that file's diff section, with its name and content, is kept in the stored diff blob. The ticket's Definition of rejected forbids an excluded path's name or content appearing in a stored diff blob. (do instead: Decode quoted header paths as UTF-8 bytes, for example `ast.literal_eval('b' + part).decode('utf-8', 'surrogateescape')`, or turn the literal_eval result back into the real path with `.encode('latin-1').decode('utf-8')`. Add a test case in tests/unit/test_runner_attempt_manifest.py where a non-ASCII excluded path is dropped from the blob.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "1ef01373d65a40ae240f4bcd3f4725a0879503c4",
  "stem": "training-attempt-manifest",
  "reviewed_sha": "1ef01373d65a40ae240f4bcd3f4725a0879503c4",
  "summary": "The manifest model, store reader and writer, harvest hook, docs and tests meet the criteria, but git-quoted non-ASCII paths are decoded into mojibake, so a user exclude glob with non-ASCII characters can fail to match and the file's content gets stored.",
  "findings": [
    {
      "code": "leak",
      "path": "clutch/runner.py",
      "line": 579,
      "message": "By default git C-quotes non-ASCII path bytes as octal escapes (core.quotePath=true), for example \"a/secr\\303\\251t.key\". `ast.literal_eval` turns each escape into a Latin-1 code point, giving 'a/secrÃ©t.key' instead of the UTF-8 path 'a/secrét.key'. The ASCII default globs still match. A configured `training_data.exclude` pattern containing non-ASCII characters (for example 'secrét*') never matches the decoded path, so that file's diff section, with its name and content, is kept in the stored diff blob. The ticket's Definition of rejected forbids an excluded path's name or content appearing in a stored diff blob.",
      "paved_road": "Decode quoted header paths as UTF-8 bytes, for example `ast.literal_eval('b' + part).decode('utf-8', 'surrogateescape')`, or turn the literal_eval result back into the real path with `.encode('latin-1').decode('utf-8')`. Add a test case in tests/unit/test_runner_attempt_manifest.py where a non-ASCII excluded path is dropped from the blob.",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.8",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
