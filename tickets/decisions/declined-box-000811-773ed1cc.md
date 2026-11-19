---
id: declined-box-000811-773ed1cc
kind: declined
link: box-000811-773ed1cc
reopen_after_days: 30
---
During the dispatch-during-driver-pass Implement run, the agent noticed that row 160 of the planning document docs/roadmap.md still describes serve's old driver admission hold, which that change replaced. The file was outside the ticket's scope fence, so the run could not fix it.

This is stale wording in a planning document. It does not change runtime behavior: no engine code parses roadmap row Content prose to decide admission, so the old description cannot make serve or drain behave wrongly. The registry has consistently declined the same class of report (out-of-fence planning-doc wording made stale by a merged change), for example 000622, 000624, 000627, 000646, 000652 and 000656. Reopen if the stale row 160 text is shown to mislead an Author draft, a requisition review or a supervising session into a wrong ticket or verdict, or if a docs-truth or release-audit row picks up roadmap row wording.

- Message class suggestion, origin dispatch-during-driver-pass, stage implement, outcome ok: the run itself succeeded.
- dispatch-during-driver-pass, dispatch-during-driver-pass-drain and dispatch-during-driver-pass-gate are all in the merged set, so the behavior change has landed.
- Precedent declines for stale docs/roadmap.md row wording after a merge: declined-box-000622-dfa19f13 (row 100), declined-box-000624-9eb8a90f (row 101), declined-box-000613-0126575c, declined-box-000656-4a757059.
- No reachable incorrect runtime behavior is named; the message proposes no paths and reports no failure.

Message: box-000811-773ed1cc
