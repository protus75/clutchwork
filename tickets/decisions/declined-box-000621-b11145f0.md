---
id: declined-box-000621-b11145f0
kind: declined
link: box-000621-b11145f0
reopen_after_days: 30
---
While implementing cadences-count-runs, the agent saw that the roadmap entry in docs/roadmap.md still describes the old wall-clock retro 'elapsed' trigger and its old configuration. That change replaced the trigger with run counts. The agent could not update the planning document because it was outside the ticket's scope fence.

This is stale wording in a forward-looking planning document. It does not change runtime behavior: the engine does not read docs/roadmap.md's prose description of the retro trigger, so no run, gate, or verb behaves incorrectly because of it. The registry has repeatedly declined the same class of out-of-fence planning-doc staleness note, for example declined-box-000613-0126575c (stale roadmap.md line after test-gate-floors-measured), declined-box-000616-3cc90496 (stale roadmap.md scheduler description), declined-box-000447-54115f00 and declined-box-000594-ac4726ce. Reopen if a roadmap parser, driver step, or gate starts reading this entry's text and acts wrongly on the old trigger or configuration, or if an operator or Author run is shown to have configured or authored work from the stale description.

- Message origin is cadences-count-runs, which is in the merged set, at stage implement with outcome ok. The ticket landed.
- The report names only docs/roadmap.md prose, which is planning documentation and not engine input for retro triggering.
- The registry declined matching out-of-fence planning-doc staleness reports: declined-box-000613-0126575c, declined-box-000616-3cc90496, declined-box-000447-54115f00, declined-box-000594-ac4726ce, declined-box-000605-4e62ffe8.
- The message cites no failed run, misconfiguration, or wrong runtime behavior caused by the stale text.

Message: box-000621-b11145f0
