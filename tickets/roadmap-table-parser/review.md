# Review: snag

clutch/roadmap.py correctly does everything the ticket asks, but several unit tests check less than their acceptance criteria require, so a regression in what goes unchecked would still pass.

## Findings

- [acceptance] tests/unit/test_roadmap_table.py:73 Criterion 5 requires that after each edit, the input's and the result's `splitlines(keepends=True)` lists differ only at index `row.line`. The test checks `link(text, c)` only for a substring and never checks that every other line is unchanged. (do instead: Compare `text.splitlines(keepends=True)` with `link(text, c).splitlines(keepends=True)` at every index except `c.line` and assert they are equal.)
- [acceptance] tests/unit/test_roadmap_table.py:78 For `strike(linked, a2)`, the test checks only the lines after `a.line` (`[a.line + 1 :]`). The lines before the edited row are never compared, so criterion 5's 'differ only at index row.line' is only partly checked for this strike. (do instead: Also assert `merged.splitlines(keepends=True)[: a.line] == linked.splitlines(keepends=True)[: a.line]`, or use one helper that compares every index except `row.line`.)
- [acceptance] tests/unit/test_roadmap_table.py:81 `strike(text, d)` (Stem cell linked through a Markdown link) is checked only for a substring and its parsed flags. Criterion 5's check that only the row's own line changes is never made for this edit, and neither is the check on `strike(text, a)` at line 84. (do instead: Apply the same every-other-line-unchanged check to `strike(text, d)` against `d.line` and to `strike(text, a)` against `a.line`.)
- [acceptance] tests/unit/test_roadmap_table.py:71 Criterion 5 says that after `link` on a plain row, `parse` reports it linked 'with its other fields unchanged'. The test checks only `linked` and `content`. It never checks number, stem, owner, kind, priority, depends, runs_before, or struck. (do instead: Assert that `a2` equals `replace(a, linked=True, content=...)`, or compare each field of `a2` with `a` except `linked` and `content`.)
- [acceptance] tests/unit/test_roadmap_table.py:42 Criterion 2 says 'The struck rows' number, stem, and content carry no `~~`'. The test checks only `e-row` (`rows[4]`). It never checks that `d-row`'s stem or `f-row`'s content (`~~Work.~~`) come back with the `~~` removed. (do instead: Also assert `rows[3].stem == 'd-row'` and `rows[5].content == 'Work.'`, or assert that no struck row has `~~` in its number, stem, or content.)
- [acceptance] tests/unit/test_roadmap_table.py:134 Criterion 8 requires that `t-row` is in no list while `s-two` is `running`. The test checks only `ready == ()` (and `strike == ()`). It never checks that `t-row` is absent from `link` and `waits`. (do instead: Also assert `choice.link == ()` and `choice.waits == ()`, or that `t-row`'s stem is in none of strike, link, ready, or the waits' rows.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "f3c97edae9bb6b19e830ae3e597c2c25087f1105",
  "stem": "roadmap-table-parser",
  "reviewed_sha": "f3c97edae9bb6b19e830ae3e597c2c25087f1105",
  "summary": "clutch/roadmap.py correctly does everything the ticket asks, but several unit tests check less than their acceptance criteria require, so a regression in what goes unchecked would still pass.",
  "findings": [
    {
      "code": "acceptance",
      "path": "tests/unit/test_roadmap_table.py",
      "line": 73,
      "message": "Criterion 5 requires that after each edit, the input's and the result's `splitlines(keepends=True)` lists differ only at index `row.line`. The test checks `link(text, c)` only for a substring and never checks that every other line is unchanged.",
      "paved_road": "Compare `text.splitlines(keepends=True)` with `link(text, c).splitlines(keepends=True)` at every index except `c.line` and assert they are equal.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/unit/test_roadmap_table.py",
      "line": 78,
      "message": "For `strike(linked, a2)`, the test checks only the lines after `a.line` (`[a.line + 1 :]`). The lines before the edited row are never compared, so criterion 5's 'differ only at index row.line' is only partly checked for this strike.",
      "paved_road": "Also assert `merged.splitlines(keepends=True)[: a.line] == linked.splitlines(keepends=True)[: a.line]`, or use one helper that compares every index except `row.line`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/unit/test_roadmap_table.py",
      "line": 81,
      "message": "`strike(text, d)` (Stem cell linked through a Markdown link) is checked only for a substring and its parsed flags. Criterion 5's check that only the row's own line changes is never made for this edit, and neither is the check on `strike(text, a)` at line 84.",
      "paved_road": "Apply the same every-other-line-unchanged check to `strike(text, d)` against `d.line` and to `strike(text, a)` against `a.line`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/unit/test_roadmap_table.py",
      "line": 71,
      "message": "Criterion 5 says that after `link` on a plain row, `parse` reports it linked 'with its other fields unchanged'. The test checks only `linked` and `content`. It never checks number, stem, owner, kind, priority, depends, runs_before, or struck.",
      "paved_road": "Assert that `a2` equals `replace(a, linked=True, content=...)`, or compare each field of `a2` with `a` except `linked` and `content`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/unit/test_roadmap_table.py",
      "line": 42,
      "message": "Criterion 2 says 'The struck rows' number, stem, and content carry no `~~`'. The test checks only `e-row` (`rows[4]`). It never checks that `d-row`'s stem or `f-row`'s content (`~~Work.~~`) come back with the `~~` removed.",
      "paved_road": "Also assert `rows[3].stem == 'd-row'` and `rows[5].content == 'Work.'`, or assert that no struck row has `~~` in its number, stem, or content.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/unit/test_roadmap_table.py",
      "line": 134,
      "message": "Criterion 8 requires that `t-row` is in no list while `s-two` is `running`. The test checks only `ready == ()` (and `strike == ()`). It never checks that `t-row` is absent from `link` and `waits`.",
      "paved_road": "Also assert `choice.link == ()` and `choice.waits == ()`, or that `t-row`'s stem is in none of strike, link, ready, or the waits' rows.",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
