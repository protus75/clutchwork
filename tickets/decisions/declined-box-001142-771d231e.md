---
id: declined-box-001142-771d231e
kind: declined
link: box-001142-771d231e
reopen_after_days: 30
---
After the merged panel-facts-journal-signal change, the planning document docs/roadmap.md still says panel facts go only to the engine log. That change now journals them as a signal. The Implement run, which ended ok, could not edit the roadmap because the file was outside its scope fence.

This is stale wording in a forward-looking planning document. It causes no incorrect runtime behavior, and the run ended ok. Earlier stale-plan-wording notes about docs/roadmap.md were declined for the same reason (for example records 000613, 000622, 000811, 000822, 001112, 001125 and 001131). Reopen if a runtime path, gate or prompt reads that roadmap sentence and acts wrongly because of it.

- message class suggestion, stage implement, outcome ok, origin panel-facts-journal-signal
- panel-facts-journal-signal is in the merged set
- docs/roadmap.md is a planning document; stale plan wording was declined in records 000613, 000622, 000811, 000822, 001112, 001125 and 001131
- neighbors unavailable (index_unreadable); not used as grounds

Message: box-001142-771d231e
