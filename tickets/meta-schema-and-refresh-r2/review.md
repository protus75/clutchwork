# Review: snag

The two prior findings are fixed, but the Python block parser swallows any comment lines that follow the block, the refresh refusal gives no next step, and the new host-running.md row is missing a table column.

## Findings

- [logic] clutch/meta.py:43 The Python block parser keeps reading lines until one does not start with `# `. It never stops after the header line plus seven key lines. When a file's body starts with a comment right after the docstring (or at the top of a file with no docstring), for example `# section` or `# noqa ...`, `refresh` inserts a valid block that is followed by that comment. The next `parse` reads the comment as part of the block, sees more than seven key lines and raises `Malformed`. As a result, `check` reports a file that `refresh` just wrote as `malformed`, and a second `refresh` refuses it with exit 2. A file's own leading comments therefore make it impossible to annotate. (do instead: Read exactly `len(KEYS)` lines after `# clutch:meta`. Each must start with `# `, or the block is malformed. Treat everything after them as body. Add a unit test in `tests/unit/test_meta_refresh.py` for a Python file whose body starts with a `# comment` line: refresh it, then check that `parse` succeeds and a second refresh returns `([], [])`.)
- [logic] clutch/__main__.py:1048 The `meta refresh` refusal prints only `clutch meta refresh: <path>: malformed`. It has no ` -- <what to do instead>` part. `docs/how-clutch-works.md` section 2 says every refusal prints `clutch <verb>: <message> -- <what to do instead>`, and the fail-closed rule requires a refusal to say what to do next. (do instead: Add a next step to the message, for example `... -- fix or remove the block so it has schema plus the six keys with a valid kind, then rerun clutch meta refresh`.)
- [acceptance] clutch/docs/host-running.md:39 The new `meta` row has two cells, but the table has three columns (`Verb | Works while serve runs? | What it does`). The description lands in the 'Works while serve runs?' column and the row says nothing about whether `meta` can run while serve runs. (do instead: Split it into two rows with three cells each: `meta refresh` | No | ... (it takes the writer lock) and `meta check` | Yes | ... (read-only).)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "16a9971637d29256d5ec0fc8ac7533e1eab27dda",
  "stem": "meta-schema-and-refresh-r2",
  "reviewed_sha": "16a9971637d29256d5ec0fc8ac7533e1eab27dda",
  "summary": "The two prior findings are fixed, but the Python block parser swallows any comment lines that follow the block, the refresh refusal gives no next step, and the new host-running.md row is missing a table column.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/meta.py",
      "line": 43,
      "message": "The Python block parser keeps reading lines until one does not start with `# `. It never stops after the header line plus seven key lines. When a file's body starts with a comment right after the docstring (or at the top of a file with no docstring), for example `# section` or `# noqa ...`, `refresh` inserts a valid block that is followed by that comment. The next `parse` reads the comment as part of the block, sees more than seven key lines and raises `Malformed`. As a result, `check` reports a file that `refresh` just wrote as `malformed`, and a second `refresh` refuses it with exit 2. A file's own leading comments therefore make it impossible to annotate.",
      "paved_road": "Read exactly `len(KEYS)` lines after `# clutch:meta`. Each must start with `# `, or the block is malformed. Treat everything after them as body. Add a unit test in `tests/unit/test_meta_refresh.py` for a Python file whose body starts with a `# comment` line: refresh it, then check that `parse` succeeds and a second refresh returns `([], [])`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "clutch/__main__.py",
      "line": 1048,
      "message": "The `meta refresh` refusal prints only `clutch meta refresh: <path>: malformed`. It has no ` -- <what to do instead>` part. `docs/how-clutch-works.md` section 2 says every refusal prints `clutch <verb>: <message> -- <what to do instead>`, and the fail-closed rule requires a refusal to say what to do next.",
      "paved_road": "Add a next step to the message, for example `... -- fix or remove the block so it has schema plus the six keys with a valid kind, then rerun clutch meta refresh`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "clutch/docs/host-running.md",
      "line": 39,
      "message": "The new `meta` row has two cells, but the table has three columns (`Verb | Works while serve runs? | What it does`). The description lands in the 'Works while serve runs?' column and the row says nothing about whether `meta` can run while serve runs.",
      "paved_road": "Split it into two rows with three cells each: `meta refresh` | No | ... (it takes the writer lock) and `meta check` | Yes | ... (read-only).",
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
