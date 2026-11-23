---
id: declined-box-001007-c547823e
kind: declined
link: box-001007-c547823e
reopen_after_days: 30
---
The merge-dirty-checkout-never-blocks Implement run, which ended ok, noted that docs/how-clutch-works.md describes how merge handles a dirty main checkout but does not mention the config.yaml exemption that change added. The run did not edit the document because it was outside its scope fence.

This is documentation drift only. The note names no wrong runtime behavior, no misled run and no operator decision that went wrong. Merge already behaves as the merged ticket specifies, whatever the document says. Earlier stale-sentence reports about docs/how-clutch-works.md were declined on the same grounds (registry records 000403, 000903 and 000998). A later ticket that edits the merge section can correct the sentence. Reopen if a run, review or operator action is shown to have gone wrong because the document leaves out the config.yaml exemption.

- The message class is suggestion, origin merge-dirty-checkout-never-blocks, stage implement, outcome ok.
- merge-dirty-checkout-never-blocks is in the merged set.
- Precedents: declined-box-000403-d925564b, declined-box-000903-fb95a382 and declined-box-000998-620886e1 declined stale how-clutch-works.md sentences that caused no runtime harm.
- No open ticket or registry record covers this specific sentence. Neighbor index unavailable.

Message: box-001007-c547823e
