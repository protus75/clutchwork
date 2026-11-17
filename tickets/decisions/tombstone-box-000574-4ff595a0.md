---
id: tombstone-box-000574-4ff595a0
kind: tombstone
link: declined-box-000457-e922cb8b
reopen_after_days: 14
---
The integration test tests/integration/test_serve_dispatch.py::test_kill_aborts_requested_retro sometimes timed out waiting for its scripted boundary during a full-suite run. It passed when rerun on its own. This time it was seen during the closed-sets-single-owner-refile Implement run. The report includes no timeout output, traceback or suspected cause.

The registry already holds this flake. Record declined-box-000457-e922cb8b declined it: one failure that passed on rerun, with no evidence. Tombstones box-000529 and box-000531 linked later sightings to it, and box-000531 matched this one word for word: an intermittent wait for the scripted boundary in the full suite that passed in isolation. This report adds no assertion, traceback, timing data or cause. It is one more sighting of a decided problem, so I am linking it to the existing record and not opening a new ticket. Reopen if a report brings the failure output or timing evidence that ties the timeout to a cause, or if the flake rate grows enough to block Check runs.

- message summary: full integration suite intermittently timed out waiting for the scripted boundary in test_kill_aborts_requested_retro; isolated rerun passed
- declined-box-000457-e922cb8b: same test failed once in provider-failure-single-mapper Check, passed on rerun, no traceback or cause
- tombstone-box-000531-54d4b6b6: identical description (intermittent timeout waiting for scripted boundary in full suite, passed alone) linked to declined-box-000457-e922cb8b
- tombstone-box-000529-fc244696: same test timing out in roadmap-table-parser run, linked to declined-box-000457-e922cb8b
- message carries no failure output, traceback, or timing data

Message: box-000574-4ff595a0
