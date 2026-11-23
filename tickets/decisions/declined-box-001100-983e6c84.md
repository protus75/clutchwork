---
id: declined-box-001100-983e6c84
kind: declined
link: box-001100-983e6c84
reopen_after_days: 30
---
Proposes that ticket review of a ticket which deletes a shared work list (here the PENDING list of test files still to move onto the shared git fake) check that every remaining entry is fenced by that ticket or by a ticket it depends on. The trigger was the shared-git-fake-unit-2..6 and -integration split. Five listed test files (test_retry_keeps_branch, test_serve_verdict_orphan_sweep, test_check_meta_fill, test_runner_verdict_reread, test_serve_verdict_owned) were assigned to no ticket, and the last ticket in the chain deleted PENDING.

This asks for a new authoring and review rule, prompted by one chain split. It shows no current harm to runtime behavior. Every shared-git-fake-unit-* ticket and shared-git-fake-integration are merged. The message names no failed run, red Check or spent cap caused by the unassigned entries, and it does not say whether those five files still keep a local fake or whether any guard fails on main. The work involved is test-harness migration, which is test-only. Earlier proposals for single-incident fence-closure and review rules were declined for the same reasons: 001094 (fence every importer of a fenced test module), 000619 (grep for removed journal records), 000388 and 000773. Reopen if a run fails Check, or main goes red, because a list-retiring ticket dropped entries no ticket covers. Reopen also if the same unassigned-entry gap happens again in another chain split, with the run or ticket named.

- shared-git-fake, shared-git-fake-unit-2 to -6 and shared-git-fake-integration are all in the merged set
- The message cites no failed attempt, Check output or spent cap caused by the five unassigned files
- Declined records 001094, 000619, 000388 and 000773 turned down similar fence-closure or review-rule requests based on one incident
- The affected work is test-harness migration, which is test-only unless it is tied to incorrect runtime behavior

Message: box-001100-983e6c84
