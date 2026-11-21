---
id: declined-box-000903-fb95a382
kind: declined
link: box-000903-fb95a382
reopen_after_days: 30
---
The merge-tree-check-ignores-ticket-plane Implement run, which ended ok, reported that step 5 of the merge sequence in docs/how-clutch-works.md (now line 595) still says main's tree must equal the checked tree. After that change, the comparison leaves out the ticket plane, so the sentence is slightly out of date. The run could not edit the file because it was outside its scope fence.

This is only a stale sentence in a document. It causes no wrong runtime behavior: the merge code already carries the ticket-plane exclusion, and nothing reads this sentence to make a decision. The registry has declined the same kind of finding before, including box-000403, another stale sentence in docs/how-clutch-works.md that a run could not fix because the file was outside its fence. The next ticket that touches merge or section 4/6 of the doc can correct the wording. Reopen if an operator or agent acts wrongly because of this sentence, for example a Review snag or a Diagnose lesson that cites it as the merge contract.

- docs/how-clutch-works.md:595 reads: 'Squash-merge as in section 4.5, and verify `main`'s tree equals the checked tree.'
- merge-tree-check-ignores-ticket-plane is in the merged set, and the run's outcome was ok
- Precedent: declined-box-000403-d925564b (a stale how-clutch-works.md sentence outside the fence) and many declined plan-doc staleness notes such as 000811 and 000822

Message: box-000903-fb95a382
