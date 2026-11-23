---
id: tombstone-box-001015-76982bbe
kind: tombstone
link: declined-box-001007-c547823e
reopen_after_days: 30
---
A note from the merge-dirty-checkout-never-blocks run says docs/how-clutch-works.md still says config.yaml falls under the general refusal for a dirty main checkout. The merged change added an exemption for config.yaml, so that statement is now out of date.

Registry record 001007 already declined this documentation gap: how-clutch-works.md leaves out the config.yaml dirty-checkout exemption that merge-dirty-checkout-never-blocks added. Records 001009 and 001011 tombstoned the same report from that run. This message repeats it in different words. The problem is a documentation mismatch only, with no wrong runtime behavior. Reopen if an operator or agent acts on the stale sentence and that causes a wrong merge decision or a wasted run.

- declined-box-001007-c547823e: same document, same config.yaml exemption, same origin run
- tombstone-box-001009-707a106e and tombstone-box-001011-51b7d4bc already link duplicates of this report to 001007
- merge-dirty-checkout-never-blocks is in the merged set; the message reports outcome ok with no runtime failure

Message: box-001015-76982bbe
