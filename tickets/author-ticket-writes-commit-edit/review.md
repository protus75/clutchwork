# Review: snag

The commit_edit migration for Author publication, compensation and decision records is correct, but the evidence listing and copied-evidence reads were moved out of the guarded try block, so their failures now bypass compensation and the decline path.

## Findings

- [logic] clutch/author.py:508 The roadmap evidence `ls-files` call (lines 506-509) and the `copied = {p: (checkout.repo / p).read_bytes() ...}` snapshot (line 513) now run before the `try:` around `driver.effects.run(commit, ...)`. Before this diff the listing ran inside `commit()` within that try, so a GitError there went to cleanup and then `failure_declined("commit failed: ...")`. Now a GitError from the listing, or an OSError from reading a copied evidence file, escapes `author()` uncaught. The gate-copied candidate evidence stays on disk, `author_gate.copied` is never cleared, and the message is never declined. This is a regression in publication-failure behavior, which acceptance criterion 2 requires to be preserved. (do instead: Keep this read-only preparation outside the lock, but put the path listing and the copied-bytes snapshot inside the same `try` that handles publication failure, or wrap them in their own handler that runs the same compensation and `failure_declined` path. Add a case to tests/unit/test_ticket_write_consumers_author.py where the evidence listing raises GitError and assert that Author declines and removes the owned evidence.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "3daed32a240ce8c6797168381d99b520d2b6e5da",
  "stem": "author-ticket-writes-commit-edit",
  "reviewed_sha": "3daed32a240ce8c6797168381d99b520d2b6e5da",
  "summary": "The commit_edit migration for Author publication, compensation and decision records is correct, but the evidence listing and copied-evidence reads were moved out of the guarded try block, so their failures now bypass compensation and the decline path.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/author.py",
      "line": 508,
      "message": "The roadmap evidence `ls-files` call (lines 506-509) and the `copied = {p: (checkout.repo / p).read_bytes() ...}` snapshot (line 513) now run before the `try:` around `driver.effects.run(commit, ...)`. Before this diff the listing ran inside `commit()` within that try, so a GitError there went to cleanup and then `failure_declined(\"commit failed: ...\")`. Now a GitError from the listing, or an OSError from reading a copied evidence file, escapes `author()` uncaught. The gate-copied candidate evidence stays on disk, `author_gate.copied` is never cleared, and the message is never declined. This is a regression in publication-failure behavior, which acceptance criterion 2 requires to be preserved.",
      "paved_road": "Keep this read-only preparation outside the lock, but put the path listing and the copied-bytes snapshot inside the same `try` that handles publication failure, or wrap them in their own handler that runs the same compensation and `failure_declined` path. Add a case to tests/unit/test_ticket_write_consumers_author.py where the evidence listing raises GitError and assert that Author declines and removes the owned evidence.",
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
