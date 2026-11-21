# Review: snag

All three earlier findings are fixed and the code matches the spec, but the integration test never checks that the real vss/HNSW embedding path returns the nearest chunk, and the unit tie test would pass with no hits at all.

## Findings

- [acceptance] tests/integration/test_index_neighbors_fulltext.py:43 Criterion 7 requires the real embedding path, with the real `vss` extension and a persisted HNSW index, to return the nearest chunk. The rebuild uses the default `Exec`, which gives every chunk and the query the same vector `[1,2,3]`, so every candidate scores 1.0 and no chunk is nearer than another. The test only asserts `result.hits` is non-empty, so a ranking that ignores the vectors would still pass. (do instead: Rebuild with an exec that returns a vector based on the text it reads from `stdin_path`, so the flaky box message gets a vector different from the others. Then query with that vector and assert `result.hits[0].ref == flaky` and `result.hits[0].score > result.hits[1].score` in `embedding` mode.)
- [logic] tests/unit/test_index_neighbors.py:114 The tie-order check only asserts that `result.hits` is in `selector` order. It never checks that any hits came back, so an empty result passes and the check proves nothing about how ties are broken. (do instead: Before the sortedness check, assert `result.outcome == "found"` and that the three tied hits (box, roadmap, decision, each scoring 0.0) are returned in `selector` ascending order.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "4c8869b7192bd50b2b8777f97a00a05e41314aac",
  "stem": "index-box-neighbors-query",
  "reviewed_sha": "4c8869b7192bd50b2b8777f97a00a05e41314aac",
  "summary": "All three earlier findings are fixed and the code matches the spec, but the integration test never checks that the real vss/HNSW embedding path returns the nearest chunk, and the unit tie test would pass with no hits at all.",
  "findings": [
    {
      "code": "acceptance",
      "path": "tests/integration/test_index_neighbors_fulltext.py",
      "line": 43,
      "message": "Criterion 7 requires the real embedding path, with the real `vss` extension and a persisted HNSW index, to return the nearest chunk. The rebuild uses the default `Exec`, which gives every chunk and the query the same vector `[1,2,3]`, so every candidate scores 1.0 and no chunk is nearer than another. The test only asserts `result.hits` is non-empty, so a ranking that ignores the vectors would still pass.",
      "paved_road": "Rebuild with an exec that returns a vector based on the text it reads from `stdin_path`, so the flaky box message gets a vector different from the others. Then query with that vector and assert `result.hits[0].ref == flaky` and `result.hits[0].score > result.hits[1].score` in `embedding` mode.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "tests/unit/test_index_neighbors.py",
      "line": 114,
      "message": "The tie-order check only asserts that `result.hits` is in `selector` order. It never checks that any hits came back, so an empty result passes and the check proves nothing about how ties are broken.",
      "paved_road": "Before the sortedness check, assert `result.outcome == \"found\"` and that the three tied hits (box, roadmap, decision, each scoring 0.0) are returned in `selector` ascending order.",
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
