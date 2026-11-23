---
id: declined-box-001069-327a44e1
kind: declined
link: box-001069-327a44e1
reopen_after_days: 30
---
Proposes an invariant test for serve's orphan sweep. The test would list every serve path that writes ticket-keyed effect intents and assert that each one holds a boundary that keeps the sweep away, meaning admission.busy() or Restart.owned() is true while it runs. Commit 99c9d7ec broke this unstated rule when it moved verdict settlement onto its own worker. The sweep then saw the confirmation's open intents and journaled a draft being confirmed as abandoned. Merged ticket reconcile-spares-confirming-draft fixed that one writer.

This is a test-only prevention measure. The one bug it points to, the sweep abandoning a draft while it is being confirmed, is already fixed by merged ticket reconcile-spares-confirming-draft. The message names no other serve writer of ticket-keyed intents that runs outside a sweep-excluding boundary today, so it shows no current, reachable wrong behavior for the test to catch. The neighbor index was unavailable, which is not a reason to decline. Reopen if any other intent writer is shown to be swept as an orphan: a journaled abandoned terminal, or an audit one_terminal_per_run violation caused by a writer running outside admission.busy() or Restart.owned(). Reopen also if a ticket in the backlog moves an intent writer onto a new worker or off an existing boundary.

- Merged stems include reconcile-spares-confirming-draft, the instance fix for the confirming-draft sweep race (registry tombstones 001057 and 001062 link to it).
- The message cites only one broken writer (verdict settlement moved by 99c9d7ec) and that one is already repaired.
- Triage bar: a test-only improvement is declined unless it is tied to reachable incorrect runtime behavior. No second current writer outside a boundary is shown.
- Neighbors block: unavailable (index_unreadable), so there is no neighbor evidence either way.

Message: box-001069-327a44e1
