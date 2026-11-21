# Review: snag

The prior finding is fixed: the evidence listing and snapshot now run inside the publication try, and the listing and snapshot tests cover them. But compensation still removes the candidate's empty directories after commit_edit returns, outside the writer locks.

## Findings

- [logic] clutch/author.py:560 After the compensation `commit_edit` returns, the loop over `(directory / "evidence", directory)` checks whether each folder is empty and then calls `folder.rmdir()`. It does this without holding main_write or commit.lock. This ticket makes ticket-plane writes happen only inside commit_edit, so another writer can be inside its own commit_edit callback at the same time. That writer's `LocalFileSystem.write` creates `tickets/<stem>/` with `mkdir(parents=True)` and then opens a temp file there. If this rmdir runs between those two steps, the other writer's write fails. If the folder gains an entry between the emptiness check and `rmdir`, the rmdir raises OSError, which escapes the `except` handler. Then `author()` raises, and `failure_declined` never runs for the message. That breaks the ticket's rule that compensation changes the tree only inside commit_edit. (do instead: Move the empty-directory removal into the `compensate` callback, after the unlinks, so it runs under both locks. Add a check to tests/unit/test_ticket_write_consumers_author.py that the directory removal happens while `git.locked` is true.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "2ea69f8b1f2f28247280d5223ef26e06873af790",
  "stem": "author-ticket-writes-commit-edit",
  "reviewed_sha": "2ea69f8b1f2f28247280d5223ef26e06873af790",
  "summary": "The prior finding is fixed: the evidence listing and snapshot now run inside the publication try, and the listing and snapshot tests cover them. But compensation still removes the candidate's empty directories after commit_edit returns, outside the writer locks.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/author.py",
      "line": 560,
      "message": "After the compensation `commit_edit` returns, the loop over `(directory / \"evidence\", directory)` checks whether each folder is empty and then calls `folder.rmdir()`. It does this without holding main_write or commit.lock. This ticket makes ticket-plane writes happen only inside commit_edit, so another writer can be inside its own commit_edit callback at the same time. That writer's `LocalFileSystem.write` creates `tickets/<stem>/` with `mkdir(parents=True)` and then opens a temp file there. If this rmdir runs between those two steps, the other writer's write fails. If the folder gains an entry between the emptiness check and `rmdir`, the rmdir raises OSError, which escapes the `except` handler. Then `author()` raises, and `failure_declined` never runs for the message. That breaks the ticket's rule that compensation changes the tree only inside commit_edit.",
      "paved_road": "Move the empty-directory removal into the `compensate` callback, after the unlinks, so it runs under both locks. Add a check to tests/unit/test_ticket_write_consumers_author.py that the directory removal happens while `git.locked` is true.",
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
