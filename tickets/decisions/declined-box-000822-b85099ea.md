---
id: declined-box-000822-b85099ea
kind: declined
link: box-000822-b85099ea
reopen_after_days: 30
---
During the storm-producer-one-builder Implement run, which ended ok, the agent reported that the planning document docs/roadmap.md still describes how the storm producer was put together before that change. The file was outside the ticket's scope fence, so the run left it unchanged.

This is a stale-wording mismatch in a planning document. It is not a runtime behavior gap: no engine path reads docs/roadmap.md's prose about storm producer composition, and the message names no wrong engine behavior or failed run that follows from it. The registry has declined the same class of report many times: 000447, 000452, 000616, 000621, 000622, 000652, 000656, 000811 and 000819 each reported a planning doc left stale by a merged change whose fence did not include the doc. Reopen if a stage, gate or Author/driver run is shown to act on this stale roadmap text and produce a wrong result, or if a roadmap row driven from it is mis-authored.

- Message class suggestion, origin storm-producer-one-builder, stage implement, outcome ok
- storm-producer-one-builder is in the merged set
- Same-class precedents: declined-box-000622-dfa19f13, declined-box-000656-4a757059, declined-box-000811-773ed1cc, declined-box-000819-6bea5b25 (stale planning-doc wording outside fence)
- No proposed_paths, no fixed_failure, no report attached

Message: box-000822-b85099ea
