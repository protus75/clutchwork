---
id: declined-box-000530-c9630ad6
kind: declined
link: box-000530-c9630ad6
reopen_after_days: 30
---
During the supervise-cap-lineage Implement run, the agent reported that section 1 of docs/roadmap-driver-plan.md still describes cap lineage as operator-only. The merged supervise-cap-lineage change has made that out of date, but the agent could not fix the plan document because it was outside the ticket's scope fence.

This is a wording mismatch in a forward-looking plan document. No engine code reads that text, so the stale sentence causes no incorrect runtime behavior and has no measurable runtime effect, which the admission bar requires. It matches earlier declines of stale roadmap-driver-plan wording (declined-box-000526-6842d927 and declined-box-000456-99370dbf). The next ticket that edits docs/roadmap-driver-plan.md under the documentation-follows-changes rule can fix it. Reopen within 30 days if the roadmap driver or any other engine component starts treating this section's lineage text as an input, or if the stale text leads an operator or agent to take a wrong action on cap lineage.

- Message class is suggestion, origin supervise-cap-lineage, stage implement, outcome ok: the run succeeded, and this is a second-problem note about a file outside its fence.
- supervise-cap-lineage is in the merged set.
- Earlier stale wording in docs/roadmap-driver-plan.md was declined as a plan-wording mismatch: declined-box-000526-6842d927 and declined-box-000456-99370dbf.
- No reproducible runtime failure or misrouted run is cited.

Message: box-000530-c9630ad6
