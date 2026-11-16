---
id: declined-box-000474-7b7f321a
kind: declined
link: box-000474-7b7f321a
reopen_after_days: 60
---
The scope-fence set-membership rule appears twice: once in the requisition review spec (clutch/specs/requisition_review.md line 24) and once in the Scope fence bullet of the host authoring guide (clutch/docs/host-authoring.md line 55). The note asks that the rule have one home, either by rendering the guide's section into the review prompt or by adding a test that the two texts stay equal. Without that, a future edit could change one copy and not the other, and requisition review would then judge tickets against a different rule from the one authors follow.

The note describes a risk that could happen later, not a fault that exists now. On current main the two copies match word for word: the trigger list, the in-code registry clause added by fence-closure-registries, and both 'not a hit' limit sentences. Both widenings so far (set-membership-fence-closure, fence-closure-registries) changed both files in the same commit. No review run is cited where a snag or approval came from a gap between the two texts. A rendering refactor or an equality test is cleanup or test-only work that fixes no wrong runtime behavior today. The open ticket requisition-review-set-limit-pin already pins the limit sentence on the review side. Reopen if the two copies differ on main, or if a requisition review snag or approval is traced to a rule that the authoring guide states differently or does not state.

- clutch/specs/requisition_review.md:24 holds the full set-membership rule, including the in-code registry clause and both limit sentences
- clutch/docs/host-authoring.md:55 holds byte-identical rule text inside the Scope fence bullet
- Merged set-membership-fence-closure and fence-closure-registries each changed both copies, which still agree
- The message names no run where review and the guide disagreed; its harm is conditional ('If one copy drifts')
- Open ticket requisition-review-set-limit-pin already adds a pin on the review-side limit sentence

Message: box-000474-7b7f321a
