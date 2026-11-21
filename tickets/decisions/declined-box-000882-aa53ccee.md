---
id: declined-box-000882-aa53ccee
kind: declined
link: box-000882-aa53ccee
reopen_after_days: 14
---
On meta-fill-surface, five Review attempts in a row each raised a new set of one or two defects, even though the review spec asks for every defect in one reply. Each retry rebuilt the change from the merge base, which brought in new defects. The note suggests three possible fixes to evaluate: a second review pass in the same attempt that looks for what the first pass missed, a rework that patches the earlier diff instead of rebuilding it, or a review that lists, for each acceptance criterion, the test that proves it and the untrusted inputs it checked.

The incident is real, but the message does not ask for one buildable ticket. It lists three candidate fixes that change different surfaces: a second review pass changes review stage orchestration, patch-based rework changes the retry and worktree model, and a per-criterion checklist changes the review spec and reply schema. None has been chosen. Fix (b) is the same request as declined-box-000795, which asked that a review-snag retry keep the reviewed diff. declined-box-000757 also declined the closely related request to re-check every requirement on retry. The evidence comes from one ticket, and meta-fill-surface has since merged, so no run is blocked now. The rule this note says was broken already exists: the merged review-all-findings ticket put it in clutch/specs/review.md. A spec change alone therefore has no proven post-change measurement. Reopen when a second ticket shows the same pattern, meaning three or more review snags in a row with findings that do not overlap, in a retro window. The reopened message should name one chosen fix and the measurement it is judged by, for example the median number of review snags per merged ticket.

- Message cites clutch/specs/review.md:21, which already requires reporting every defect in one reply; merged ticket review-all-findings owns that rule.
- meta-fill-surface is in the merged set, so the incident no longer blocks a run.
- Candidate (b), patching the prior diff instead of rebuilding from the merge base, duplicates declined-box-000795-bdd30fe6.
- declined-box-000757-6b98d911 declined a related request after a later review raised requirements the earlier one had not.
- declined-box-000879-9f900b70 already declined the authoring-rule follow-up from the same meta-fill-surface attempt 0.
- The message lists three alternative fixes as 'candidate fixes to evaluate', not one bounded change.

Message: box-000882-aa53ccee
