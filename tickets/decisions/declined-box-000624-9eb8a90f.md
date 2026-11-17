---
id: declined-box-000624-9eb8a90f
kind: declined
link: box-000624-9eb8a90f
reopen_after_days: 30
---
During the eval-go-ai-panel Implement run, the agent noticed that row 101 of docs/roadmap.md still describes the operator approval flag that the change removed. The note says the row is waiting for the roadmap driver to update it.

The message reports stale wording in a planning document. Nothing in clutch reads that row's prose at runtime, and no command or operator decision goes wrong because of it. The registry has already declined the same class of report several times: stale roadmap or plan rows left behind by a merged change (000613, 000621, 000622, 000594, 000616). The note also says the roadmap driver is expected to update the row, so no separate ticket is needed. Reopen if the stale row 101 text causes wrong runtime behavior, such as roadmap.parse or choose acting on it or an Author draft built from it, or if the row is still stale after the driver has processed eval-go-ai-panel's merge.

- Message class suggestion, origin eval-go-ai-panel, stage implement, outcome ok: a stale doc row noted while implementing a change that has since merged.
- eval-go-ai-panel is in the merged set.
- Precedent declines for stale docs/roadmap.md rows after merges: declined-box-000613-0126575c, declined-box-000621-b11145f0, declined-box-000622-dfa19f13.
- The message names no runtime consumer of the row's prose and no wrong behavior.

Message: box-000624-9eb8a90f
