---
id: declined-box-000551-0deb538b
kind: declined
link: box-000551-0deb538b
reopen_after_days: 30
---
Under drain and run, a rebase conflict at merge leaves no record of which paths conflicted. `merge.merge` calls `MergeQueue._admit` with `conflict_facts=False`, so no `merge_conflict_facts` signal is written. The `rebase onto main refused:` finding keeps only `exc.err`. On git 2.43, the `CONFLICT (content): Merge conflict in <path>` lines go to stdout, and stderr carries only `error: could not apply ...`. Only serve, which journals conflict facts, matches the plan's claim that each conflict is recorded.

The code matches the report. `clutch/merge.py:287` passes `conflict_facts=False`, and `clutch/mergequeue.py:313` builds the refusal from `exc.err.strip()` only. But this is a gap in what gets recorded, not wrong behavior that has caused harm. The evidence file shows 566 merges with 0 refusals for `post_rebase_regate` or `rebase onto main refused`. No `CONFLICT (` lines appear anywhere. Main never moved under a run, because drain is single-flight. If a drain conflict did happen, the ticket would still fail closed (a `gate_failed` refusal with a paved road to re-run), so nothing merges wrong. The only consumer that needs the data is the merge-model-resolve roadmap row, which is not yet a ticket, and the evidence says its conflict data is expected from serve with parallel scheduling, and serve already records facts. A wording mismatch with the plan and an observability gap with no incident fall below the admission bar. Reopen if any drain or run merge journals a `rebase onto main refused` refusal whose conflicting paths the operator or Diagnose cannot recover. Also reopen when a merge-model-resolve or parallel-drain ticket is authored that needs conflict facts from the inline path.

- clutch/merge.py:287 passes conflict_facts=False to MergeQueue._admit
- clutch/mergequeue.py:290-292: facts() writes only when conflict_facts is true; line 313 builds the refusal message from exc.err (stderr) only
- tickets/merge-model-resolve/evidence/merge-conflict-facts.md finding 3: 566 merges, 0 post_rebase_regate refusals, 0 'rebase onto main refused', 0 'CONFLICT (' lines; main never moved under a run
- same file, 'What the design can rest on' item 2: real conflict data begins with serve plus scheduler.parallel, and serve's path already records conflict facts
- same file, item 4: git 2.43 probe puts CONFLICT lines on stdout and 'error: could not apply' on stderr (confirmed as a fact, but no observed failure depends on it)

Message: box-000551-0deb538b
