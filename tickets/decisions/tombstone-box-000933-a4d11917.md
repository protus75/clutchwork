---
id: tombstone-box-000933-a4d11917
kind: tombstone
link: serve-confirm-during-check
reopen_after_days: 14
---
A session audit asks for three changes so that serve's exclusive sections stop waiting for running implementations. (a) Every engine path that writes a ticket file and then commits it should run under one lock that intake also takes. (b) Serve's scan and watch publication should no longer take admission.exclusive(). (c) Verdict settlement, which applies confirm and reject, should leave the exclusive merge poll and register with admission idle/abort. Merged tickets already cover all three parts.

Every part of this request already has a merged ticket. serve-confirm-during-check moves control.poll and settle_admissions out of the merge transaction into a dedicated Serve.verdicts worker that never enters admission.exclusive or mutations. That ticket relies on a prerequisite that already protects the ticket writers. That prerequisite work is covered by the merged ticket-writer stems runner-ticket-writes-commit-edit, rework-ticket-writes-commit-edit, author-ticket-writes-commit-edit, git-commit-edit-owner and ticket-write-serialization-proof. serve-scan-watch-off-exclusive takes scan and watch off exclusive(): scan reads under main_write() and watch publishes under scheduler._slot. The earlier instance, box-000916, was already tombstoned to serve-confirm-during-check, and box-000880 was tombstoned to serve-polls-block-parallel-runs. Reopen if, with these merges in place, serve still fails to run two implementations at once or delays a confirm until a running implementation finishes, and a journal or engine-log trace shows it.

- tickets/serve-confirm-during-check/ticket.md:48 moves control.poll and settle_admissions to a Serve.verdicts worker that uses the prerequisite's protected ticket writers and never admission.exclusive or mutations
- tickets/serve-scan-watch-off-exclusive/ticket.md:47 says scan and watch never enter admission.exclusive() or mutations(), scan reads under git.main_write(), and watch holds scheduler._slot
- the merged stems include serve-confirm-during-check, serve-scan-watch-off-exclusive, serve-merge-off-exclusive, serve-polls-block-parallel-runs, runner-ticket-writes-commit-edit, rework-ticket-writes-commit-edit, author-ticket-writes-commit-edit, git-commit-edit-owner and ticket-write-serialization-proof
- registry records tombstone-box-000916-dce84ab8 (link serve-confirm-during-check) and tombstone-box-000880-c564bbf8 (link serve-polls-block-parallel-runs) cover the cited related messages

Message: box-000933-a4d11917
