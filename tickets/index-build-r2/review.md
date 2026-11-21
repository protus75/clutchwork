# Review: snag

The build mostly follows the ticket, but the Markdown chunker treats `#` lines inside fenced code blocks as headings, and the seam-restriction test cannot catch most of the `os.`, `subprocess` and `time.` uses that criterion 11 requires it to fail on.

## Findings

- [logic] clutch/index.py:81 The heading regex `(?m)^#{1,6}[ \t]+(.+?)...$` runs over the whole Markdown text and does not track code fences. A `# comment` line inside a ```python or ```bash block in a doc therefore becomes a heading. That creates a bogus chunk with a selector like `docs/x.md#comment` and cuts the real section's text short at that point. The ticket asks for one chunk per heading, and a line inside a fenced code block is not a heading. The regex also drops a trailing `#` that is part of the heading text, such as `# C#`, which it records as `C`. (do instead: Walk the text line by line, toggling an in-fence flag on lines whose stripped form starts with ``` (the same check tickets.py and stages.py already use), and treat only out-of-fence ATX lines as headings. Strip a closing `#` run only when whitespace comes before it. Add a unit test with a fenced `# comment` that must not produce a chunk.)
- [acceptance] tests/integration/test_index_extensions.py:74 Criterion 11 requires the source scan to fail on any `os.`, `subprocess`, `time.` or `datetime.now` use. This check only fails on a direct call of the form `os.X(...)`, `subprocess.X(...)` or `time.X(...)`. It still passes for `os.path.exists(p)` (the call's func is a nested Attribute), `os.environ[...]`, `import subprocess` / `from subprocess import run`, `from time import monotonic`, and a `time.monotonic` reference that is never called. For those cases the test cannot fail. (do instead: Fail on every `ast.Attribute` whose base `ast.Name` is `os`, `subprocess` or `time`, whether or not it is called, and on every `ast.Import`/`ast.ImportFrom` of `os`, `subprocess`, `time` or `datetime`. Alternatively, also assert that the source text contains none of `os.`, `subprocess`, `time.` or `datetime.now`.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "8faa3611f5f3f2fab6a35e6d215da1ba13dfbd6d",
  "stem": "index-build-r2",
  "reviewed_sha": "8faa3611f5f3f2fab6a35e6d215da1ba13dfbd6d",
  "summary": "The build mostly follows the ticket, but the Markdown chunker treats `#` lines inside fenced code blocks as headings, and the seam-restriction test cannot catch most of the `os.`, `subprocess` and `time.` uses that criterion 11 requires it to fail on.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/index.py",
      "line": 81,
      "message": "The heading regex `(?m)^#{1,6}[ \\t]+(.+?)...$` runs over the whole Markdown text and does not track code fences. A `# comment` line inside a ```python or ```bash block in a doc therefore becomes a heading. That creates a bogus chunk with a selector like `docs/x.md#comment` and cuts the real section's text short at that point. The ticket asks for one chunk per heading, and a line inside a fenced code block is not a heading. The regex also drops a trailing `#` that is part of the heading text, such as `# C#`, which it records as `C`.",
      "paved_road": "Walk the text line by line, toggling an in-fence flag on lines whose stripped form starts with ``` (the same check tickets.py and stages.py already use), and treat only out-of-fence ATX lines as headings. Strip a closing `#` run only when whitespace comes before it. Add a unit test with a fenced `# comment` that must not produce a chunk.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/integration/test_index_extensions.py",
      "line": 74,
      "message": "Criterion 11 requires the source scan to fail on any `os.`, `subprocess`, `time.` or `datetime.now` use. This check only fails on a direct call of the form `os.X(...)`, `subprocess.X(...)` or `time.X(...)`. It still passes for `os.path.exists(p)` (the call's func is a nested Attribute), `os.environ[...]`, `import subprocess` / `from subprocess import run`, `from time import monotonic`, and a `time.monotonic` reference that is never called. For those cases the test cannot fail.",
      "paved_road": "Fail on every `ast.Attribute` whose base `ast.Name` is `os`, `subprocess` or `time`, whether or not it is called, and on every `ast.Import`/`ast.ImportFrom` of `os`, `subprocess`, `time` or `datetime`. Alternatively, also assert that the source text contains none of `os.`, `subprocess`, `time.` or `datetime.now`.",
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
