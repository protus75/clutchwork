---
id: declined-box-000802-cfb6465b
kind: declined
link: box-000802-cfb6465b
reopen_after_days: 30
---
The note asks requisition or ticket review to check that each acceptance criterion's bound uses the same phase and threshold as the check that measures it, and to report a mismatch under its own finding code. It cites two cases from 2026-11-19. host-loop-scenarios-concurrent compared a setup-only 8s bound with a 10s cap that covers setup, call and teardown. measure-snapshot-at-journal-checkpoint documented a 1s threshold, but its regression script passes at a median under 2s.

Both cited tickets parked at requisition, so the existing requisition review already caught both mismatches before any Implement call or cap was spent. host-loop-scenarios-concurrent has since merged. Nothing shows a phase or threshold mismatch getting past review and causing wrong runtime behavior or a wasted run. A dedicated finding code would only rename a defect class the reviewer already catches. That is speculative hardening of the review spec, not a fix for a current harmful gap. Reopen if an approved ticket fails at Implement, Check or merge because a criterion bounds a different phase or threshold than its check measures.

- The message says both host-loop-scenarios-concurrent and measure-snapshot-at-journal-checkpoint parked at requisition on 2026-11-19, which means requisition review caught both.
- host-loop-scenarios-concurrent is in the merged stems, so its mismatch was fixed through the normal review loop.
- The message cites no ticket that passed review with a mismatched criterion and then failed later.

Message: box-000802-cfb6465b
