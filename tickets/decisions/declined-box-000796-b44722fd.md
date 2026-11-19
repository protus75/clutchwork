---
id: declined-box-000796-b44722fd
kind: declined
link: box-000796-b44722fd
reopen_after_days: 3
---
The confirmed ticket measure-snapshot-at-journal-checkpoint is still blocked because its only `## Depends on` entry, snapshot-duckdb-under-one-second, was rejected. The two open tickets that replaced that work are snapshot-from-duckdb-cache and journal-duckdb-cache.

The block is real: the dependent is confirmed, and its dependency's ticket file says `state: rejected`. But the fix is an edit to the existing ticket, not a new piece of work. The dependent's `## Depends on` should name the replacement work (snapshot-from-duckdb-cache, which owns the snapshot latency target) in place of the rejected stem, or the ticket should be re-scoped. That edit belongs to whoever supervises the ticket, using `clutch prompt diagnose`. Writing a new ticket for it would duplicate the existing one. The engine itself has no defect here: the depends hold is doing what it should. Reopen if the dependent is still blocked after its Depends on is changed to a live stem, or if the replacement tickets are rejected too.

- tickets/measure-snapshot-at-journal-checkpoint/ticket.md: state confirmed; `## Depends on` lists only snapshot-duckdb-under-one-second
- tickets/snapshot-duckdb-under-one-second/ticket.md: state rejected
- The open tickets snapshot-from-duckdb-cache and journal-duckdb-cache both cite tickets/snapshot-duckdb-under-one-second/evidence/snapshot-incident-profile.txt as their source, so they replace that work

Message: box-000796-b44722fd
