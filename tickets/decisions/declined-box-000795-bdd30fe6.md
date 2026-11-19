---
id: declined-box-000795-bdd30fe6
kind: declined
link: box-000795-bdd30fe6
reopen_after_days: 30
---
When Review raises a snag on an attempt that passed Check, the retry throws away the reviewed diff and Implement rebuilds the whole change from main. The note asks that a review-snag retry keep the reviewed branch or diff, so Implement changes only what the findings name. The trigger was document-agent-roadmap-prompt attempt 1 (2026-11-19). Its only rejected part was where the README entry was placed.

The engine does exactly what it was designed to do. `prepare_worktree` in clutch/stages.py removes any earlier worktree and branch, then creates a new branch from main. clutch/specs/diagnose.md:32 says every attempt starts from the merge base and that lessons must not say to build on an earlier diff. So the request is to change a policy, not to fix a fault. The one incident cost only the time to redo the work: document-agent-roadmap-prompt has since merged, and the message shows no retry that broke something new because it was rebuilt from scratch. The fix would also be more than one ticket. It would touch worktree preparation, whether a kept branch is still current with main and how it handles conflicts, the diagnose and implement specs, and the run sequence and spool numbering. The note gives nothing to measure before and after, such as how many retries failed on new ground. Reopen if the journal shows review-snag retries that fail or reach the Reject queue because of a problem that did not exist in the reviewed attempt, or that spend measurably more attempts than a targeted amend would need.

- clutch/stages.py:490-505 prepare_worktree: 'TEARDOWN-AND-CREATE: remove any worktree and branch a prior run left, then branch from main'
- clutch/specs/diagnose.md:32: 'Every attempt starts from the merge base, so no earlier diff survives; lessons must not say to keep or build on a previous diff'
- tickets/document-agent-roadmap-prompt/diagnosis.json attempt 1: verdict retry, lesson 0 'Redo the whole change from the merge base' and lists the parts Review found sound
- document-agent-roadmap-prompt is in the merged set, so the incident resolved on retry with no failure on new ground shown

Message: box-000795-bdd30fe6
