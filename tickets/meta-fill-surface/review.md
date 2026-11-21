# Review: snag

The diff covers most criteria, but fill builds its blocks through a second composition path that skips the generator's Python relates trim, and it accepts a blank owner that the next refresh would rewrite.

## Findings

- [acceptance] clutch/metafill.py:111 fill throws away the `result` that `meta.generated` returns and builds the block a second time with `body[:offset] + meta._render(...) + body[offset:]`. The ticket's Scope in asks for one shared helper that both refresh and fill call for block rendering. Its Definition of rejected forbids 'a second code path for composing blocks'. (do instead: Have the shared helper in clutch/meta.py compose the block from fields and body, including the .py relates trim. Call it from both `generated`/refresh and fill, after fill merges the reply into the fields.)
- [logic] clutch/metafill.py:107 For a file whose generated `relates` is empty, fill copies the model's `entry.relates` in unchanged. For a `.py` file this skips the generator's rule that drops entries until `# relates: [...]` fits in 160 characters. A long model-supplied list therefore writes a Python block line the refresh path would never produce. (do instead: Apply the same 160-character trim to model-supplied relates for .py files, through the shared composition helper, before writing.)
- [logic] clutch/metafill.py:99 The owner check only rejects newlines and `-->`, so a blank or whitespace-only `owner` passes. Line 109 then replaces the default `engine` with it. The next `meta refresh` sees an empty owner and recomputes it, so a file fill reported as filled is not stable under refresh. That rewrite is exactly the drift the later Check-time refresh would flag. (do instead: Reject an entry whose owner is blank after strip, or keep `engine` when the reply's owner is blank. Add a test case for it.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "9db3fae04a404c60c8f537bce36fa40abe45343d",
  "stem": "meta-fill-surface",
  "reviewed_sha": "9db3fae04a404c60c8f537bce36fa40abe45343d",
  "summary": "The diff covers most criteria, but fill builds its blocks through a second composition path that skips the generator's Python relates trim, and it accepts a blank owner that the next refresh would rewrite.",
  "findings": [
    {
      "code": "acceptance",
      "path": "clutch/metafill.py",
      "line": 111,
      "message": "fill throws away the `result` that `meta.generated` returns and builds the block a second time with `body[:offset] + meta._render(...) + body[offset:]`. The ticket's Scope in asks for one shared helper that both refresh and fill call for block rendering. Its Definition of rejected forbids 'a second code path for composing blocks'.",
      "paved_road": "Have the shared helper in clutch/meta.py compose the block from fields and body, including the .py relates trim. Call it from both `generated`/refresh and fill, after fill merges the reply into the fields.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "clutch/metafill.py",
      "line": 107,
      "message": "For a file whose generated `relates` is empty, fill copies the model's `entry.relates` in unchanged. For a `.py` file this skips the generator's rule that drops entries until `# relates: [...]` fits in 160 characters. A long model-supplied list therefore writes a Python block line the refresh path would never produce.",
      "paved_road": "Apply the same 160-character trim to model-supplied relates for .py files, through the shared composition helper, before writing.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "clutch/metafill.py",
      "line": 99,
      "message": "The owner check only rejects newlines and `-->`, so a blank or whitespace-only `owner` passes. Line 109 then replaces the default `engine` with it. The next `meta refresh` sees an empty owner and recomputes it, so a file fill reported as filled is not stable under refresh. That rewrite is exactly the drift the later Check-time refresh would flag.",
      "paved_road": "Reject an entry whose owner is blank after strip, or keep `engine` when the reply's owner is blank. Add a test case for it.",
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
