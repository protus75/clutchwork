---
id: declined-box-000856-7a722dd4
kind: declined
link: box-000856-7a722dd4
reopen_after_days: 30
---
After one-parser-per-provider-live merged, an Implement run reported that two planning documents, docs/evidence-trail-plan.md and docs/roadmap.md, still say live_call parses provider process arguments. The run could not update either file because both were outside its scope fence.

Both files are planning documents, so this is a plan-wording mismatch. The note names no wrong runtime behavior. The registry has declined the same kind of report many times: stale planning-document wording left by a ticket whose fence did not include the plan (000447, 000594, 000605, 000613, 000621, 000622, 000811, 000822, 000836, 000904). Reopen if a stage, prompt or operator acts on these two passages and that produces wrong runtime behavior, or if the stale wording is cited as authority in a failed run.

- Message class suggestion from the one-parser-per-provider-live Implement run, which ended ok
- one-parser-per-provider-live is in the merged set
- Same kind of report as declined records 000447, 000594, 000605, 000613, 000621, 000622, 000811, 000822, 000836 and 000904
- No runtime failure, wrong output or failed run is cited

Message: box-000856-7a722dd4
