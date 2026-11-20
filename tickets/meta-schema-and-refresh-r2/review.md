# Review: snag

The diff is well wired, but the block parser accepts a block anywhere in the file, and generated `relates` resolves `from clutch import x` to the package `__init__.py` instead of the imported module.

## Findings

- [logic] clutch/meta.py:26 `block()` uses `re.search` with a multiline `^`, so it treats the first `<!-- clutch:meta` / `# clutch:meta` found anywhere in the file as the file's block. The ticket places the block at the top of a Markdown file (after any frontmatter) and, in Python, after the docstring or at the top. `docs/annotations-index-plan.md` is under the configured `docs/` root and has a valid example block inside a fenced code sample at lines 35-43. `check` reports that file as `drifted` instead of `missing`. `refresh` rewrites the example's `kind`, `verified` and `hash` in the middle of the plan document and never inserts the file's real block. The same happens for a Python file with a line-start marker inside a string, and line 29 raises `Malformed` for any line-start marker in body text. (do instead: Look for the block only at the insertion position `_position` computes (offset 0, right after the closing frontmatter fence, or right after the Python docstring), e.g. with `re.match` anchored at that offset. Text elsewhere is body. Add a unit test where a fenced example block in the body stays untouched and the file is reported `missing`.)
- [logic] clutch/meta.py:78 For `ast.ImportFrom`, only `node.module` is resolved, so `from clutch import meta` (the dominant import form in `tests/`, more than 250 files) yields `clutch/__init__.py` instead of `clutch/meta.py`. Generated `relates` then misses the repo modules the file actually imports, and `owner` becomes `clutch/__init__.py`. Because a non-empty `relates`/`owner` is never rewritten, the wrong values stick. (do instead: For `ImportFrom`, also try `module + '.' + alias.name` for each imported name (mapping to `<path>.py` or `<path>/__init__.py`), keeping the package path only when no submodule matches. Cover `from clutch import foo` in `tests/unit/test_meta_refresh.py`.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "15ae83568045a39e9f0b739c218351566505581f",
  "stem": "meta-schema-and-refresh-r2",
  "reviewed_sha": "15ae83568045a39e9f0b739c218351566505581f",
  "summary": "The diff is well wired, but the block parser accepts a block anywhere in the file, and generated `relates` resolves `from clutch import x` to the package `__init__.py` instead of the imported module.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/meta.py",
      "line": 26,
      "message": "`block()` uses `re.search` with a multiline `^`, so it treats the first `<!-- clutch:meta` / `# clutch:meta` found anywhere in the file as the file's block. The ticket places the block at the top of a Markdown file (after any frontmatter) and, in Python, after the docstring or at the top. `docs/annotations-index-plan.md` is under the configured `docs/` root and has a valid example block inside a fenced code sample at lines 35-43. `check` reports that file as `drifted` instead of `missing`. `refresh` rewrites the example's `kind`, `verified` and `hash` in the middle of the plan document and never inserts the file's real block. The same happens for a Python file with a line-start marker inside a string, and line 29 raises `Malformed` for any line-start marker in body text.",
      "paved_road": "Look for the block only at the insertion position `_position` computes (offset 0, right after the closing frontmatter fence, or right after the Python docstring), e.g. with `re.match` anchored at that offset. Text elsewhere is body. Add a unit test where a fenced example block in the body stays untouched and the file is reported `missing`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "clutch/meta.py",
      "line": 78,
      "message": "For `ast.ImportFrom`, only `node.module` is resolved, so `from clutch import meta` (the dominant import form in `tests/`, more than 250 files) yields `clutch/__init__.py` instead of `clutch/meta.py`. Generated `relates` then misses the repo modules the file actually imports, and `owner` becomes `clutch/__init__.py`. Because a non-empty `relates`/`owner` is never rewritten, the wrong values stick.",
      "paved_road": "For `ImportFrom`, also try `module + '.' + alias.name` for each imported name (mapping to `<path>.py` or `<path>/__init__.py`), keeping the package path only when no submodule matches. Cover `from clutch import foo` in `tests/unit/test_meta_refresh.py`.",
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
