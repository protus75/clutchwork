# Review: snag

The prior missing-blob finding is fixed and the code meets the acceptance criteria, but the four new rows in host-running.md wrongly say the evidence verbs don't work while serve runs.

## Findings

- [logic] clutch/docs/host-running.md:46 The new `evidence show` row puts `no` in the table's 'Works while serve runs?' column (header at line 12). The verb takes no lock and writes nothing, so it does work while serve runs. Similar no-lock read verbs such as `training export` and `meta check` say `Yes`. The row tells operators the opposite of what the code does. (do instead: Set the second column of the `evidence show` row to `Yes`.)
- [logic] clutch/docs/host-running.md:47 The new `evidence schema` row puts `no` in the 'Works while serve runs?' column, but the verb only prints a schema and takes no lock, so it works while serve runs. (do instead: Set the second column of the `evidence schema` row to `Yes`.)
- [logic] clutch/docs/host-running.md:48 The new `evidence renormalize` row puts `no` in the 'Works while serve runs?' column, but the handler takes no lock (the ticket says 'No lock, no journal event'), so it works while serve runs. (do instead: Set the second column of the `evidence renormalize` row to `Yes`.)
- [logic] clutch/docs/host-running.md:49 The new `evidence coverage` row puts `no` in the 'Works while serve runs?' column, but the verb takes no lock and writes nothing, so it works while serve runs. (do instead: Set the second column of the `evidence coverage` row to `Yes`.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "4bb46f7218ef83da4f0aa1fe72a4c85a5d216dc8",
  "stem": "evidence-verbs",
  "reviewed_sha": "4bb46f7218ef83da4f0aa1fe72a4c85a5d216dc8",
  "summary": "The prior missing-blob finding is fixed and the code meets the acceptance criteria, but the four new rows in host-running.md wrongly say the evidence verbs don't work while serve runs.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/docs/host-running.md",
      "line": 46,
      "message": "The new `evidence show` row puts `no` in the table's 'Works while serve runs?' column (header at line 12). The verb takes no lock and writes nothing, so it does work while serve runs. Similar no-lock read verbs such as `training export` and `meta check` say `Yes`. The row tells operators the opposite of what the code does.",
      "paved_road": "Set the second column of the `evidence show` row to `Yes`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "clutch/docs/host-running.md",
      "line": 47,
      "message": "The new `evidence schema` row puts `no` in the 'Works while serve runs?' column, but the verb only prints a schema and takes no lock, so it works while serve runs.",
      "paved_road": "Set the second column of the `evidence schema` row to `Yes`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "clutch/docs/host-running.md",
      "line": 48,
      "message": "The new `evidence renormalize` row puts `no` in the 'Works while serve runs?' column, but the handler takes no lock (the ticket says 'No lock, no journal event'), so it works while serve runs.",
      "paved_road": "Set the second column of the `evidence renormalize` row to `Yes`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "clutch/docs/host-running.md",
      "line": 49,
      "message": "The new `evidence coverage` row puts `no` in the 'Works while serve runs?' column, but the verb takes no lock and writes nothing, so it works while serve runs.",
      "paved_road": "Set the second column of the `evidence coverage` row to `Yes`.",
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
