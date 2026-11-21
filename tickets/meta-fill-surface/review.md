# Review: snag

The three earlier findings are fixed: one shared compose helper, the .py trim applied to model-supplied relates, and blank owners rejected. Two smaller defects remain: the README sentence the diff edited is now garbled, and the review_reply test cannot catch an 'extra' finding that leaves out its path.

## Findings

- [acceptance] README.md:20 The edited sentence lost its comma and now reads 'Use `clutch meta refresh` to update configured file metadata `clutch meta check` to report missing, empty or drifted blocks, and ...'. It runs two verbs together, so the README no longer states correctly what `meta refresh` and `meta check` do. (do instead: Restore the list punctuation: 'Use `clutch meta refresh` to update configured file metadata, `clutch meta check` to report missing, empty or drifted blocks, and `clutch meta fill` to fill them using a read-only model.')
- [logic] tests/unit/test_meta_fill.py:87 The check `all(any(p in f.message for f in report.findings) for p in ("a", "b"))` uses the one-letter path "a", and "a" is a substring of the label "extra". The assertion still passes if the extra-path finding leaves out the path, or if the missing and extra findings are swapped. Criterion 4 requires the failing report to name the offending path, and this test cannot fail when it doesn't. (do instead: Use path names that cannot appear in the labels (e.g. "docs/asked.md" and "docs/added.md"). Assert on the exact finding messages, such as {f.message for f in report.findings} == {"missing: docs/asked.md", "extra: docs/added.md"}.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "f8dc3325748bf7fe13d2cccf6d0dc00e44e0d60f",
  "stem": "meta-fill-surface",
  "reviewed_sha": "f8dc3325748bf7fe13d2cccf6d0dc00e44e0d60f",
  "summary": "The three earlier findings are fixed: one shared compose helper, the .py trim applied to model-supplied relates, and blank owners rejected. Two smaller defects remain: the README sentence the diff edited is now garbled, and the review_reply test cannot catch an 'extra' finding that leaves out its path.",
  "findings": [
    {
      "code": "acceptance",
      "path": "README.md",
      "line": 20,
      "message": "The edited sentence lost its comma and now reads 'Use `clutch meta refresh` to update configured file metadata `clutch meta check` to report missing, empty or drifted blocks, and ...'. It runs two verbs together, so the README no longer states correctly what `meta refresh` and `meta check` do.",
      "paved_road": "Restore the list punctuation: 'Use `clutch meta refresh` to update configured file metadata, `clutch meta check` to report missing, empty or drifted blocks, and `clutch meta fill` to fill them using a read-only model.'",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "tests/unit/test_meta_fill.py",
      "line": 87,
      "message": "The check `all(any(p in f.message for f in report.findings) for p in (\"a\", \"b\"))` uses the one-letter path \"a\", and \"a\" is a substring of the label \"extra\". The assertion still passes if the extra-path finding leaves out the path, or if the missing and extra findings are swapped. Criterion 4 requires the failing report to name the offending path, and this test cannot fail when it doesn't.",
      "paved_road": "Use path names that cannot appear in the labels (e.g. \"docs/asked.md\" and \"docs/added.md\"). Assert on the exact finding messages, such as {f.message for f in report.findings} == {\"missing: docs/asked.md\", \"extra: docs/added.md\"}.",
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
