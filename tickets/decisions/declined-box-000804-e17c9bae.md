---
id: declined-box-000804-e17c9bae
kind: declined
link: box-000804-e17c9bae
reopen_after_days: 30
---
On 2026-11-19 the owner decided that the snapshot latency check (DuckDB cache, median under 2 s) runs once, on the ticket that delivers it, and is never a recurring test, verb or release gate. The remaining request changes documents only. docs/journal-sql-refactor-plan.md and docs/roadmap.md would say that a journal-performance checkpoint also records the end-to-end `clutch view snapshot` time, because the earlier status and drain-startup readings missed a 31 s snapshot incident. No new gate command is added and tests/integration/test_roadmap_gate.py does not change.

This asks only for new wording in two planning documents about how a manual performance checkpoint is recorded. It adds no gate, test or verb, and it changes no runtime behavior. The incident it cites, a 31 s snapshot of which journal reads took 0.18 s, has already been addressed by the merged snapshot-from-duckdb-cache and journal-duckdb-cache tickets. A change to plan wording alone does not meet the bar for authoring: nothing in it ties to engine behavior that is wrong today and reachable. The registry has repeatedly declined plan-document-only edits on the same grounds (for example 000616, 000622, 000797). Reopen if snapshot latency regresses without anyone noticing because a checkpoint left out the snapshot reading, or if the roadmap driver's journal-window rows come up for authoring and need this checkpoint definition to be decidable.

- The message limits itself to docs only: no gate command, no test change and no verb.
- Merged stems snapshot-from-duckdb-cache and journal-duckdb-cache already deliver the snapshot speed fix the incident called for.
- Registry precedents 000616, 000622 and 000797 declined plan-document-only staleness edits as having no runtime impact.
- Record 000802 already settled the rejected ticket this message replaces, measure-snapshot-at-journal-checkpoint, and its threshold dispute.

Message: box-000804-e17c9bae
