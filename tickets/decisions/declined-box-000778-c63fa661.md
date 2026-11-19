---
id: declined-box-000778-c63fa661
kind: declined
link: box-000778-c63fa661
reopen_after_days: 30
---
The merge-model-resolve ticket added resolve and review model calls inside MergeQueue._admit, which runs while the merge stage is already open. Driver.stage refused to open a stage inside another, so those calls failed under serve. The tests that assert no model calls for eligible conflicts were also outside the fence, and Implement attempt 2 was lost. The message asks for an authoring and requisition-review rule: a ticket that adds a model call must name the stage its caller already has open, say how the call runs given that stages do not nest, and fence the tests that assert no model requests on that path.

The incident is already fixed in code. clutch/driver.py:175-178 now lets a resolve or review stage open inside an open merge stage, and merge-model-resolve has merged, so the reported harmful behavior no longer happens. What remains is an authoring and requisition-review wording rule drawn from one incident. Its bad outcome was an extra attempt, not wrong runtime behavior. Earlier one-incident fence and authoring rules were declined for the same reason: box-000773 (consumers forced by ENGINE_LLM_SURFACES, which came from this same ticket), box-000555 (grep callers of changed symbols) and box-000619 (grep tests for removed journal records). Reopen if, within 30 days, a second ticket adds a model call under an open driver stage and loses an attempt or reaches the Reject queue for that reason.

- clutch/driver.py:175-178 Driver.stage now lets a resolve or review stage open under an open (stem, 'merge') stage
- merge-model-resolve is in the merged set
- Precedent declines for one-incident authoring and fence rules: box-000773, box-000555, box-000619
- The message reports one lost Implement attempt and no recurring runtime failure

Message: box-000778-c63fa661
