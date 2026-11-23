---
id: tombstone-box-001086-900ea014
kind: tombstone
link: intake-commit-lock-per-ticket
reopen_after_days: 14
---
On 2026-11-22 at 05:50:19Z serve stopped with CommitLockTimeout for a third time. Only 5 pending io-helpers-* tickets were waiting, and each intake commit took about 12 s. The total hold passed COMMIT_LOCK_WAIT_S (60 s) while the shared-git-fake worker waited. The note proposes moving per-ticket validation (_intake_plan_stem, lint) outside the commit lock, so the lock covers only the git commit.

The cause is the same one the open ticket intake-commit-lock-per-ticket fixes. `intake` holds `git._commit_lock` once across every pending stem, so the hold grows with the number of tickets. With 5 stems at about 12 s each, that is about 60 s. The open ticket splits the lock into one hold per stem and releases it between stems. Its acceptance criteria require a competing waiter to get the lock before the next stem's commit. That keeps the longest hold to about 12 s, well under 60 s, so this addendum's incident is covered. Moving validation out of the lock as well would only shorten each hold further, and nothing shows a single stem's hold coming near the timeout. The fatal-crash part is already covered by serve-commit-lock-timeout-contained. Reopen if a CommitLockTimeout happens after intake-commit-lock-per-ticket merges, with evidence that one stem's hold alone came near COMMIT_LOCK_WAIT_S.

- tickets/intake-commit-lock-per-ticket/ticket.md: Scope in splits the lock so each stem's _intake_plan_stem, stamp, commit and journal append get their own hold, released between stems
- Acceptance criterion 2 of that ticket: a waiter acquires the lock while stem two is committing, before stem three's commit starts
- Message: 5 tickets at about 12 s each, about 60 s total, which equals COMMIT_LOCK_WAIT_S; a per-stem hold of about 12 s stays far under it
- Open ticket serve-commit-lock-timeout-contained covers serve stopping on a worker CommitLockTimeout

Message: box-001086-900ea014
