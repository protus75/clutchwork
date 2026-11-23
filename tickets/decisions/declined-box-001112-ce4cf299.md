---
id: declined-box-001112-ce4cf299
kind: declined
link: box-001112-ce4cf299
reopen_after_days: 30
---
The io-helpers-config Implement run said lines 97-98 of the planning document docs/roadmap.md would still name the old owner of the helpers after the change moved them. That file is a forward-looking plan, so the stale text causes no wrong behavior at runtime.

This only reports that a planning document's wording no longer matches the code. Nothing reads docs/roadmap.md lines 97-98 at runtime to make a decision, so the mismatch causes no incorrect engine behavior. The registry has declined many reports of this same kind, where a plan document went stale after a ticket outside its fence changed the code: 000447, 000452, 000594, 000616, 000656, 000822, 000856, 000861 and 001101. io-helpers-config is merged, and the roadmap can be corrected by a doc sweep or a release audit. The premise_failed outcome on this message has no evidence that the stale roadmap text caused the bounce. Reopen if a stale ownership statement in docs/roadmap.md is shown to mislead a stage, such as Author, requisition review or the roadmap driver, into a wrong ticket or a failed run.

- The message is class suggestion, origin io-helpers-config, stage implement, and it names only stale wording at docs/roadmap.md:97-98.
- io-helpers-config is in the merged stem set.
- Earlier declines of stale planning-document wording: 000447, 000452, 000616, 000656, 000822, 001101.
- No runtime consumer, failing test or harmed run is cited.

Message: box-001112-ce4cf299
