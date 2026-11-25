---
id: declined-box-001148-cee5d96b
kind: declined
link: box-001148-cee5d96b
reopen_after_days: 30
---
The session suggests a new ticket-lint rule. Lint would refuse a `## Scope in` that tells Implement to search the repo at run time and then fence only the matches, because the fence must be complete when the ticket is authored. The trigger was requisition review parking implement-fence-gap-keeps-branch for exactly this.

The existing gate worked. Requisition review caught the deferred fence and parked the ticket before Implement ran. The ticket was then corrected and has since merged, so it costs no run today. The authoring guide (clutch/docs/host-authoring.md line 107) already tells the author to grep each changed name or value before replying, which puts fence closure at authoring time. Turning this into a lint rule would add a second check for something requisition review already enforces. It would also need lint to read intent from free prose in Scope in, which is not a clear, measurable rule. Similar requests to add more grep-and-fence enforcement were declined in box-000818 and box-001054. Reopen if lint is shown to be the only reliable guard: a ticket with a grep-then-fence Scope in gets past requisition review and loses an Implement or Check attempt, or the same review park happens twice more within 30 days.

- implement-fence-gap-keeps-branch is in the merged set and its ticket directory has run.md, checks.json and review.md, so the park was cleared
- clutch/docs/host-authoring.md:107 already says 'Before replying, grep the repo for each changed name or value', which makes the fence final at authoring
- Requisition review caught the defect before dispatch, which is the gate's intended job
- Earlier grep-then-fence enforcement requests box-000818 and box-001054 were declined

Message: box-001148-cee5d96b
