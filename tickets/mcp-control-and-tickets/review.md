# Review: snag

The implementation follows the ticket's shared-owner design, but the updated `mcp serve` row in docs/how-clutch-works.md now says the server takes the writer lock, which is wrong.

## Findings

- [acceptance] docs/how-clutch-works.md:57 In the section 2.1 verb table, the second column is `Lock`. Every other row uses lowercase `no` / `yes` / `commit only` to say whether the verb takes the writer lock. The diff changes the `mcp serve` row's Lock cell from `no` to `Yes`. The stdio server itself holds no lock: the new CLI help says `lock="Per-tool domain locks; no lock held by the stdio server."`, and only individual tools take their domain locks. The row now documents the lock behavior wrongly, so criterion 7's 'document ... accurately' is unmet. The value appears to have been copied from host-running.md's `Works while serve runs?` column. (do instead: Restore the Lock cell for `mcp serve` to `no`. If you want to say that individual tools take domain locks, put that in the description column, keeping the column's lowercase style.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "9d2f6b0b05631183b143c812f00cfd2dd97beb6b",
  "stem": "mcp-control-and-tickets",
  "reviewed_sha": "9d2f6b0b05631183b143c812f00cfd2dd97beb6b",
  "summary": "The implementation follows the ticket's shared-owner design, but the updated `mcp serve` row in docs/how-clutch-works.md now says the server takes the writer lock, which is wrong.",
  "findings": [
    {
      "code": "acceptance",
      "path": "docs/how-clutch-works.md",
      "line": 57,
      "message": "In the section 2.1 verb table, the second column is `Lock`. Every other row uses lowercase `no` / `yes` / `commit only` to say whether the verb takes the writer lock. The diff changes the `mcp serve` row's Lock cell from `no` to `Yes`. The stdio server itself holds no lock: the new CLI help says `lock=\"Per-tool domain locks; no lock held by the stdio server.\"`, and only individual tools take their domain locks. The row now documents the lock behavior wrongly, so criterion 7's 'document ... accurately' is unmet. The value appears to have been copied from host-running.md's `Works while serve runs?` column.",
      "paved_road": "Restore the Lock cell for `mcp serve` to `no`. If you want to say that individual tools take domain locks, put that in the description column, keeping the column's lowercase style.",
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
