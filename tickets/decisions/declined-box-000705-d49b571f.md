---
id: declined-box-000705-d49b571f
kind: declined
link: box-000705-d49b571f
reopen_after_days: 30
---
Two sentences in docs/how-clutch-works.md repeat rules that have a home elsewhere. Section 2.2 repeats the unit-test disk/network/process rule, which lives in the 'Unit and integration tests' section of clutch/docs/host-authoring.md. Section 12 copies, word for word, the managed-block sentence from the 'Managed conduct and ticket ownership' section of clutch/docs/host-contract.md. The note asks for both sentences to cite their home instead, perhaps under the 0.4.0 release audit.

This is documentation cleanup with no runtime effect. Both copies currently match their sources, and the integration test tests/integration/test_unit_io_rule.py already pins the unit-test copy. The note shows no engine, gate, prompt, or authoring decision that went wrong because of either copy. The merged ticket rule-restatements-single-home covered the targeted restatements. The open release-audit-040-r1 ticket covers roadmap sections 2-4, not these docs, so this is not a duplicate of it. Reopen if either copy drifts from its source and a run, review, or authoring decision follows the stale text, or if the owner adds these sections to a release audit's scope.

- Message class is suggestion, origin session; the stage, outcome, and report fields are all null.
- The note says the section 12 sentence matches host-contract.md word for word, so the two texts do not currently disagree.
- tests/integration/test_unit_io_rule.py already pins the section 2.2 copy of the unit-test I/O rule, per the message.
- rule-restatements-single-home (roadmap row 126) is merged; this note covers leftovers outside that row.
- release-audit-040-r1 covers docs/roadmap.md sections 2-4 and gate blocks, not docs/how-clutch-works.md restatements.

Message: box-000705-d49b571f
