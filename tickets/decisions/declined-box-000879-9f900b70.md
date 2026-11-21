---
id: declined-box-000879-9f900b70
kind: declined
link: box-000879-9f900b70
reopen_after_days: 30
---
This suggestion proposes an authoring rule. When a ticket requires two code paths to share one helper, the ticket would add a criterion and a test showing that neither path builds its own output. It was prompted by meta-fill-surface attempt 0: Review rejected that attempt because `fill` built the meta block by string splicing instead of calling the shared helper, which let the model's `.py` relates skip the 160-character trim and let a blank owner through.

The original problem is already fixed and merged. On current main, `clutch/metafill.py::fill` builds the block only through `meta.compose(..., trim=generated_relates)` (line 117) and rejects a blank or multi-line owner (line 105). The existing pipeline worked as intended: Review caught the splice on attempt 0, at the cost of one retry, and no wrong behavior reached main. The proposal is a preventive authoring rule backed by one incident. It shows no reachable runtime fault, which matches earlier declined authoring-rule proposals such as 000376 and 000388. Reopen if Review misses a shared-helper bypass and the result merges to main, or if this same splice snag happens again on two or more tickets within 30 days.

- clutch/metafill.py:117 fill composes via meta.compose with trim=generated_relates; no string splice remains
- clutch/metafill.py:101-106 rejects blank purpose and malformed owner
- meta-fill-surface is in the merged set; Review caught the defect on attempt 0 before merge
- Similar authoring-rule proposals declined: declined-box-000376-a635ab89, declined-box-000388-6e5d11b5

Message: box-000879-9f900b70
