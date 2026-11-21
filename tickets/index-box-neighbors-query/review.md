# Review: snag

The `neighbors` implementation matches the spec, but the unit tests leave parts of criteria 4 and 5 unasserted.

## Findings

- [acceptance] tests/unit/test_index_neighbors.py:134 Criterion 5 asks for two separate cases. In the first, a creator whose `load(conn, "vss")` returns `["vss unavailable: x"]` gives `findings[1] == "fts unavailable: index missing"`. In the second, a creator whose `load(conn, "fts")` fails gives `findings[1] == "fts unavailable: y"`. The test combines both failures in one creator, so the vss-only case with `fts unavailable: index missing` is never asserted. (do instead: Split the case into two creators. The first fails only `("load", "vss")` and asserts `findings == ("embed_failed: vss unavailable: x", "fts unavailable: index missing")`. The second fails only `("load", "fts")` while an embed failure is present and asserts `findings[1] == "fts unavailable: y"`.)
- [acceptance] tests/unit/test_index_neighbors.py:135 Criterion 5 says every fallback case returns outcome `fulltext_unavailable`, mode `""` and `hits == ()`. Only the five exec-reply cases at line 130 assert outcome, mode and hits. The vss-unavailable, fts-load-failure and embeddings-table-missing cases (lines 135 and 145) assert only `findings`. (do instead: In those cases, assert the full `(outcome, mode, hits, findings)` tuple, as line 130 does.)
- [acceptance] tests/unit/test_index_neighbors.py:121 Criterion 4 asks for `index_unreadable` with a finding starting `index_unreadable: ` for a database with no `chunks` table. The test checks only the outcome, not the finding prefix. (do instead: Keep the result and assert `result.outcome == "index_unreadable" and result.findings[0].startswith("index_unreadable: ")`, as lines 117-118 do for the other cases.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "13750fd7bbc0f0e6d34373a7facb86cd071ce142",
  "stem": "index-box-neighbors-query",
  "reviewed_sha": "13750fd7bbc0f0e6d34373a7facb86cd071ce142",
  "summary": "The `neighbors` implementation matches the spec, but the unit tests leave parts of criteria 4 and 5 unasserted.",
  "findings": [
    {
      "code": "acceptance",
      "path": "tests/unit/test_index_neighbors.py",
      "line": 134,
      "message": "Criterion 5 asks for two separate cases. In the first, a creator whose `load(conn, \"vss\")` returns `[\"vss unavailable: x\"]` gives `findings[1] == \"fts unavailable: index missing\"`. In the second, a creator whose `load(conn, \"fts\")` fails gives `findings[1] == \"fts unavailable: y\"`. The test combines both failures in one creator, so the vss-only case with `fts unavailable: index missing` is never asserted.",
      "paved_road": "Split the case into two creators. The first fails only `(\"load\", \"vss\")` and asserts `findings == (\"embed_failed: vss unavailable: x\", \"fts unavailable: index missing\")`. The second fails only `(\"load\", \"fts\")` while an embed failure is present and asserts `findings[1] == \"fts unavailable: y\"`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/unit/test_index_neighbors.py",
      "line": 135,
      "message": "Criterion 5 says every fallback case returns outcome `fulltext_unavailable`, mode `\"\"` and `hits == ()`. Only the five exec-reply cases at line 130 assert outcome, mode and hits. The vss-unavailable, fts-load-failure and embeddings-table-missing cases (lines 135 and 145) assert only `findings`.",
      "paved_road": "In those cases, assert the full `(outcome, mode, hits, findings)` tuple, as line 130 does.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/unit/test_index_neighbors.py",
      "line": 121,
      "message": "Criterion 4 asks for `index_unreadable` with a finding starting `index_unreadable: ` for a database with no `chunks` table. The test checks only the outcome, not the finding prefix.",
      "paved_road": "Keep the result and assert `result.outcome == \"index_unreadable\" and result.findings[0].startswith(\"index_unreadable: \")`, as lines 117-118 do for the other cases.",
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
