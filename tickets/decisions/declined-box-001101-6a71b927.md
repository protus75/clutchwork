---
id: declined-box-001101-6a71b927
kind: declined
link: box-001101-6a71b927
reopen_after_days: 30
---
The shared-git-fake-integration Implement run ended ok. It reported that two planning documents, docs/roadmap.md and docs/boundary-contract-plan.md, still say the retired Git fake lives in tests/fakes.py. Both files were outside that ticket's scope fence, so the run did not edit them.

This is a stale statement in a planning document. It causes no wrong runtime behavior. Earlier records declined the same kind of report: 000447, 000594, 000616, 000656, 000811, 000870 and 000964 all covered planning documents left stale by a merged change outside its fence. No engine, gate or test reads these sentences, and no run was harmed. Reopen if a ticket, prompt or gate is shown to rely on these documents and is misled into using the retired fake location, causing a failed or misrouted run.

- Message class suggestion, origin shared-git-fake-integration, stage implement, outcome ok
- Both named files are planning documents, not code or shipped guides
- Precedent declines for out-of-fence stale plan wording: declined-box-000447-54115f00, declined-box-000656-4a757059, declined-box-000964-b77f2c02
- shared-git-fake-integration is in the merged set

Message: box-001101-6a71b927
