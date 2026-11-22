---
state: confirmed
source: box:roadmap_row
priority: P0
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- docs/engine-state-db-plan.md

## On-demand
- clutch/daemon.py
- clutch/serve.py
- clutch/runner.py
- clutch/tickets.py
- clutch/git.py
- clutch/control.py
- clutch/watcher.py
- docs/how-clutch-works.md
- clutch/docs/host-running.md

## Goal / Why
Roadmap row 210, the first slice of `docs/engine-state-db-plan.md` section 7. After this change a verdict (confirm, reject, keep) and a ticket change (intake, watcher publication) complete while an implementation is running. Today `Serve.scan`, `Serve.watch` and the merge-queue `Serve.merge` no longer enter `DaemonAdmission.exclusive`; the remaining admission-wide waits are `Serve.mutations` (retro, supervision, box intake), `Serve.maintenance` (`admission.exclusive()` in `clutch/serve.py`) and the startup and orphan-sweep entries in `clutch/daemon.py`. A confirm on 2026-11-21 waited about 6 minutes for a running ticket to merge while a ready ticket with a disjoint fence did not start; this slice must leave verdict and ticket-change paths with no such wait once ticket state moves to the database.

The slice delivers the minimum end-to-end machinery, with no dual writer:
- a per-user DuckDB state database with stable project identity, keyed rows and short transactions;
- one service that owns the connection, and a local endpoint that CLI verbs use for these reads and writes;
- ticket revisions, verdict requests and checkpoint status moved into that database;
- a Git checkpoint exporter that commits only the revision's ticket path under a short project Git critical section, and dispatches a revision only after its checkpoint is committed;
- editor-conflict handling: if both the file and the database changed since the last exported base, both versions are kept, that ticket's checkpoint and dispatch are held, and the other tickets continue;
- durable recovery: an acknowledged request survives a restart, and a retry with the same request ID returns the recorded result.

Each ported path deletes its former live writer and read path in the same change. Merge queue, scheduler sets, holds and pause, and service handoff stay with their own rows (`state-merge-queue`, `state-scheduler-sets`, `state-holds-pause`, `state-service-handoff`).

## Boundary contract
### State database and service
- disposition: create
- owner: clutch/state.py
- consumers: clutch/serve.py, clutch/runner.py, clutch/tickets.py, clutch/daemon.py, CLI verbs for ticket verdicts and intake
- observable change: a per-user DuckDB file outside any checkout holds project registrations, ticket revisions, verdict requests with outcomes, and checkpoint status. Every row and uniqueness constraint includes the project key. Registration refuses ambiguous or duplicate repository identities. The service serializes short transactions and never holds one across a model call, host check, Git operation or human wait.
- compatibility: the journal, evidence spools and run records are untouched and stay authoritative history. Tickets on disk keep their format.
- acceptance: a retry with the same request ID returns the recorded result; an expected-revision mismatch is refused with a specific reason; two projects never see each other's rows.
- tests: new unit tests with an in-memory DuckDB and fake clock, Git and endpoint seams.
- post-merge source of truth: clutch/state.py
- closest existing: clutch/journal.py, clutch/journalcache.py and clutch/control.py. The journal is append-only history and the cache is a rebuildable projection. The control inbox is file-based and has no keyed mutable state or request idempotency.
- earning reason: the plan requires one process-owned mutable-state store with transactions and revision checks. No existing artifact offers this, and it is a new storage and process boundary with several production consumers.

### Endpoint and CLI access
- disposition: extend
- owner: clutch/state.py (endpoint) and clutch/__main__.py (verbs)
- consumers: ticket confirm, reject and keep verbs, intake, and the extension through CLI verbs
- observable change: these verbs submit project identity, request ID and expected revision to the service and return an acknowledged durable result or a specific refusal. If no service runs, the verb starts one and waits for readiness, or reports a clear startup or recovery failure without writing independently.
- compatibility: verb names, flags and exit codes are unchanged. Messages may name the request ID.
- acceptance: with the service down and unstartable, the verb exits non-zero and writes nothing.
- tests: unit tests against a fake endpoint; one real-socket test in a new allowlisted integration file.
- post-merge source of truth: clutch/state.py and the verb help in clutch/__main__.py

### Admission exclusion for verdicts, intake and watcher
- disposition: replace
- owner: clutch/daemon.py (`DaemonAdmission`) and clutch/serve.py
- consumers: `Serve.scan`, `Serve.watch`, verdict settlement (`Serve.verdicts`, `Serve.apply_verdict`), and `runner.verdict_locked`
- observable change: these paths do not enter `DaemonAdmission.exclusive` or `mutations`, and the ported state reads add no admission wait. Bounded run slots and the short scheduler selection remain. Startup recovery keeps a readiness barrier.
- compatibility: merge-queue processing keeps its current serialization until `state-merge-queue`. The existing ticket-changed contract for an edit during a run is preserved.
- acceptance: with a run slot held, a verdict and an intake pass complete without waiting for it.
- tests: new unit tests with held slots and fake time.
- post-merge source of truth: clutch/daemon.py and clutch/serve.py

### Git checkpoint and editor conflicts
- disposition: extend
- owner: clutch/state.py (export job) using clutch/git.py
- consumers: dispatch eligibility, review pinning of ticket blobs
- observable change: after an accepted revision the exporter writes the exact bytes to the ticket path and commits only that path. It records revision, content hash, expected parent and commit SHA. It rechecks the file hash before replacing it, and refuses and rescans rather than overwriting. An interrupted export is retried idempotently after inspecting HEAD and bytes. Both-changed conflicts keep both versions and hold only that ticket.
- compatibility: `clutch(<stem>)` commits remain the reviewed record. External edits are detected on startup, on rescan and before export.
- acceptance: the file is never overwritten when it changed during export; a crash between database commit and Git commit is repaired on restart with exactly one commit.
- tests: new unit tests using the shared Git fake.
- post-merge source of truth: clutch/state.py

## Scope in / Scope out
Scope in:
- add `clutch/state.py` with the schema, the service, the endpoint, request-ID idempotency, the checkpoint exporter and startup reconciliation;
- port the intake, verdict, watcher publication and admission paths named above, and delete their former live writers and read paths; `Serve.scan`, `Serve.watch` and verdict settlement must stay free of `DaemonAdmission.exclusive` and `mutations` (no new entry may be added);
- drain selection and dispatch (`_Drain._scan`, `_sha`, `_offer_material` in `clutch/drain.py`) dispatch only revisions whose checkpoint commit exists and skip tickets held for an editor conflict, using the `clutch/state.py` service for both checks;
- engine-written `# clutch:meta` header lines: the engine's Check meta fill rewrites the header of each edited file after Implement. Those header changes are in scope; the implementer never edits them;
- add the release path for an editor-conflict hold: `clutch ticket resolve <stem> --keep file|database` submits through the service, records the chosen version as a new revision on the recorded base, checkpoints it and releases only that ticket's hold; its help and examples and its `clutch/docs/host-running.md` verb row ship in the same change;
- update verb help and the docs that describe these commands: `clutch/docs/host-running.md` verb rows, and `docs/how-clutch-works.md` section 2 and the lock inventory;
- update the existing tests whose assertions flip because the exclusive wait is gone.

Scope out:
- merge queue, scheduler sets, holds and pause, service lifecycle, handoff and lock retirement, which remain with `state-merge-queue`, `state-scheduler-sets`, `state-holds-pause` and `state-service-handoff`;
- the journal and its SQL refactor, which stay as they are;
- the extension JavaScript.

The row asks for one slice that removes the wait with no dual writer, so it is not split further.

## Scope fence
- clutch/state.py
- clutch/serve.py
- clutch/daemon.py
- clutch/runner.py
- clutch/tickets.py
- clutch/git.py
- clutch/control.py
- clutch/watcher.py
- clutch/drain.py
- clutch/__main__.py
- clutch/help.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- docs/roadmap.md
- tests/unit/test_state_service.py
- tests/unit/test_state_verdict_no_admission_wait.py
- tests/unit/test_state_checkpoint_conflict.py
- tests/integration/test_state_endpoint.py
- tests/integration/conftest.py
- tests/unit/test_serve_scan_watch_locks.py
- tests/integration/test_serve_scan_watch_overlap.py
- tests/regress_serve_scan_watch_off_exclusive.py
- tests/regress_serve_merge_off_exclusive.py
- tests/unit/test_drain_checkpoint_dispatch.py
- tests/unit/test_drain_eligible.py
- tests/unit/test_drain_reoffer.py
- tests/unit/test_drain_containment.py

## Acceptance criteria
1. A request replayed with the same request ID returns the recorded result and creates no second revision, not a new one: `./dev.py test tests/unit/test_state_service.py`.
2. A request with a stale expected revision is refused with a named reason, not applied: `./dev.py test tests/unit/test_state_service.py`.
3. Rows for project A are never returned by a query for project B, and a duplicate or ambiguous registration is refused: `./dev.py test tests/unit/test_state_service.py`.
4. While a run slot is held, `Serve.scan` (intake) and verdict settlement both complete, and neither enters `DaemonAdmission.exclusive` or `mutations` (built from `DaemonAdmission` and in-memory fakes in a unit file, not an integration test): `./dev.py test tests/unit/test_state_verdict_no_admission_wait.py`.
5. A revision is not dispatchable until its checkpoint commit exists. The commit contains only that ticket's path: `./dev.py test tests/unit/test_state_checkpoint_conflict.py`.
6. When both the file and the database changed since the exported base, both versions are kept, the file is not overwritten, that ticket is held and another ticket still checkpoints: `./dev.py test tests/unit/test_state_checkpoint_conflict.py`.
7. After a simulated crash between the database commit and the Git commit, restart produces exactly one checkpoint commit: `./dev.py test tests/unit/test_state_checkpoint_conflict.py`.
8. With the service unstartable, a verdict verb exits non-zero and leaves the database and ticket file unchanged: `./dev.py test tests/unit/test_state_service.py`.
9. A real local endpoint round trip authenticates the client and returns the acknowledged result: `./dev.py test tests/integration/test_state_endpoint.py`.
10. No former live writer or read path remains for the ported state, and no SQLite file is opened: `./dev.py test tests/unit/test_state_service.py`.
11. Command docs and help are consistent: `./dev.py test tests/unit/test_main_help.py tests/unit/test_help.py`.
12. Drain selection and dispatch skip a revision with no checkpoint commit and a ticket held for an editor conflict, while other tickets still dispatch: `./dev.py test tests/unit/test_drain_checkpoint_dispatch.py`.
13. `clutch ticket resolve <stem> --keep file|database` records the chosen version as a new revision, checkpoints it and releases only that ticket's hold; a ticket not held is refused with a named reason: `./dev.py test tests/unit/test_state_checkpoint_conflict.py`.
14. No database transaction is open while a fake Git call, endpoint call or host check is pending: `./dev.py test tests/unit/test_state_service.py`.
15. Dispatch and verdict handling are refused until startup recovery completes, then proceed: `./dev.py test tests/unit/test_state_verdict_no_admission_wait.py`.
16. A ticket edit during a run still invalidates the pinned revision under the ticket-changed contract: `./dev.py test tests/unit/test_state_verdict_no_admission_wait.py`.
17. The exporter rechecks the file hash before replacement and refuses and rescans on change; an interrupted export retries after inspecting HEAD and bytes: `./dev.py test tests/unit/test_state_checkpoint_conflict.py`.

## Verification
```
./dev.py test tests/unit tests/integration
```

## Definition of rejected
- A branch that leaves both the old file-based writer and the database writer live for any ported path.
- A branch where a verdict or intake still waits for a held run slot.
- A branch that opens SQLite, or opens DuckDB outside the service.
- A branch that overwrites a ticket file changed by an editor.

## Time budget
- expected: 28m
- stuck: 56m
- reason: the row asks for the smallest slice that removes the admission wait with no dual writer, and splitting it would leave a dual writer; the calibration medians are about 6-10m actual per run.
