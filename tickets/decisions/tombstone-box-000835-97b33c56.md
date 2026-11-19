---
id: tombstone-box-000835-97b33c56
kind: tombstone
link: declined-box-000778-c63fa661
reopen_after_days: 30
---
The note asks for an authoring and requisition-review rule for tickets that add a model call to code that already runs inside an open Driver stage. Stages do not nest, so such a call fails with 'stage already open' (`clutch/driver.py:175-178`). This time it happened on image-candidates-select-r1, where review_visual judge calls inside Check failed at Implement and the run ended incomplete. The note says requisition review should check the stage-nesting rules and fence driver.py for any exemption.

This repeats registry record declined-box-000778-c63fa661. That record covered the same failure: merge-model-resolve added resolve and review model calls inside MergeQueue._admit while the merge stage was already open, and Driver.stage refused to nest. It also asked for the same fix, a rule that a ticket adding a model call must name the stage its caller already has open, say how the call runs given that stages do not nest, and fence the affected files. This note only adds a second incident under the Check stage. That incident is also settled: image-candidates-select-r1 is in the merged set, so no current failure needs repair. Reopen if a third ticket loses an attempt to 'stage already open' after merging, because a third incident would show this recurs often enough to need a prevention rule.

- Message cites clutch/driver.py:175-178, where an attempt to open a stage while one is already open is refused.
- Registry record declined-box-000778-c63fa661 covers the same stage-nesting failure (merge-model-resolve, MergeQueue._admit under the merge stage) and asks for the same authoring and requisition-review rule.
- image-candidates-select-r1 appears in the merged stems list, so the reported instance has been fixed.

Message: box-000835-97b33c56
