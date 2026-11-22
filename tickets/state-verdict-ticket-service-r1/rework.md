# Supervisor Rework escalated

- trigger: premise_failed
- outcome: gate_failed
- action: update

## Findings

- `supervise_edit`: the proposal changes `## Goal / Why` -- escalate to the operator: the stem stays in the Reject queue; edit tickets/state-verdict-ticket-service-r1/ticket.md, then `clutch ticket confirm state-verdict-ticket-service-r1`, or retire it with `clutch ticket reject state-verdict-ticket-service-r1`

## Proposed ticket

````markdown
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
- clutch/serve.py::Serve.scan
- clutch/serve.py::Serve.verdicts
- clutch/serve.py::Serve.apply_verdict
- tests/integration/test_tickets.py::test_bug_evidence_committed_with_ticket
- tests/integration/test_roadmap_row_author.py

## On-demand
- clutch/daemon.py
- clutch/runner.py
- clutch/tickets.py
- clutch/git.py
- clutch/control.py
- clutch/watcher.py
- clutch/drain.py
- docs/how-clutch-works.md
- clutch/docs/host-running.md

## Goal / Why
Roadmap row 210 (`state-verdict-ticket-service-r1`), the first step of the migration in section 7 of `docs/engine-state-db-plan.md`. This refiles `state-verdict-ticket-service`, which ended `premise_failed` with its premise_bounce cap spent (`tickets/state-verdict-ticket-service/diagnosis.json`, `rework.md`). That ticket's Goal misdescribed the code, so this one states the premise as read from HEAD.

Premise at HEAD: `Serve.scan`, `Serve.watch`, `Serve.merge` and `Serve.verdicts` no longer enter `DaemonAdmission.exclusive` (earlier tickets `serve-scan-watch-off-exclusive`, `serve-merge-off-exclusive` and `serve-verdicts-wait-for-runs` landed). The admission-wide entries that remain are `Serve.mutations` (retro, supervision, box intake), `Serve.maintenance`, and the startup and orphan-sweep entries in `clutch/daemon.py`. The wait seen on 2026-11-21 (a confirm applied about 6 minutes late, while a ready disjoint-fence ticket did not start) therefore comes from the checkout-wide serialization that remains: verdicts and intake write ticket files and commit under `Git.main_write` and `CommitLock`, and `Serve.watch` holds the scheduler slot through publication. The implementer must first reproduce this on the base commit in a fake-driven unit test and name the actual blocking edge in the run record. If the wait does not reproduce, that is a premise finding, not a reason to widen scope.

When this is done, verdict and ticket-change requests (confirm, reject, keep, intake, watcher publication) are acknowledged after a short DuckDB transaction and never wait on a held run slot, the merge queue, or another ticket's Git work. Their Git checkpoints are separate short per-ticket export jobs, and a revision is dispatched only once its checkpoint commit exists. This ticket delivers the minimum end-to-end machinery with no dual writer:
- a per-user DuckDB state database with stable project identity, project-keyed rows and short transactions;
- one service that owns the connection, and a local authenticated endpoint that the ticket-verdict and intake verbs use;
- ticket revisions, verdict requests with outcomes, and checkpoint status held in that database;
- a checkpoint exporter that commits only that ticket's own `tickets/<stem>/` paths (its `ticket.md` plus any of its changed evidence) under a short project Git critical section, never another ticket's paths;
- editor-conflict handling: if both the file and the database changed since the last exported base, both versions are kept, only that ticket's checkpoint and dispatch are held, and other tickets continue;
- durable recovery: an acknowledged request survives a restart, and a retry with the same request ID returns the recorded result.

Each ported path deletes its former live writer and read path in the same change. Merge queue, scheduler sets, holds and pause, and service handoff stay with `state-merge-queue`, `state-scheduler-sets`, `state-holds-pause` and `state-service-handoff`.

## Boundary contract
### State database and service
- disposition: create
- owner: clutch/state.py
- consumers: clutch/serve.py, clutch/runner.py, clutch/tickets.py, clutch/control.py, clutch/drain.py, ticket verdict and intake verbs
- observable change: a per-user DuckDB file outside any checkout holds project registrations, ticket revisions, verdict requests with outcomes, and checkpoint status. Every row and uniqueness constraint includes the project key. Registration refuses ambiguous or duplicate repository identities. The service serializes short transactions and never holds one across a model call, host check, Git operation, endpoint call or human wait.
- compatibility: the journal, evidence spools and run records are untouched and stay authoritative history. Tickets on disk keep their format.
- acceptance: a retry with the same request ID returns the recorded result; an expected-revision mismatch is refused with a specific reason; two projects never see each other's rows.
- tests: new unit tests with an in-memory DuckDB and fake clock, Git and endpoint seams.
- post-merge source of truth: clutch/state.py
- closest existing: clutch/journal.py and clutch/journalcache.py are append-only history and a rebuildable projection; clutch/control.py is a file-based inbox with no keyed mutable state or request idempotency. None offers transactions, revision checks or idempotent requests, so none can be reused.
- earning reason: the plan requires one process-owned mutable-state store with several production consumers (serve, runner, intake, drain, verbs) and a new storage and process boundary.

### Endpoint and CLI access
- disposition: extend
- owner: clutch/state.py (endpoint) and clutch/__main__.py (verbs)
- consumers: ticket confirm, reject and keep verbs, intake, the new `ticket resolve` verb, and the extension through CLI verbs
- observable change: these verbs submit project identity, request ID and expected revision to the service and return an acknowledged durable result or a specific refusal. If no service runs, the verb starts one and waits for readiness, or reports a clear startup or recovery failure without writing independently.
- compatibility: existing verb names, flags and exit codes are unchanged; messages may name the request ID.
- acceptance: with the service unstartable, the verb exits non-zero and writes nothing.
- tests: unit tests against a fake endpoint; one real-socket test in a new allowlisted integration file.
- post-merge source of truth: clutch/state.py and the verb help in clutch/__main__.py

### Admission exclusion for verdicts, intake and watcher
- disposition: reuse
- owner: clutch/daemon.py (`DaemonAdmission`) and clutch/serve.py
- consumers: `Serve.scan`, `Serve.watch`, `Serve.verdicts`, `runner.apply_admission`
- observable change: none to `DaemonAdmission`. The ported paths keep not entering `DaemonAdmission.exclusive` or `mutations`, add no new admission entry, and no longer wait on checkout-wide ticket-file or Git serialization held by other tickets. Startup recovery keeps its readiness barrier.
- compatibility: preserves the current off-exclusive behavior; merge-queue serialization is unchanged until `state-merge-queue`. The ticket-changed contract for an edit during a run is preserved.
- acceptance: with a run slot held, a verdict and an intake pass complete without waiting for it.
- tests: new unit tests with held slots and fake time.
- post-merge source of truth: clutch/serve.py

### Git checkpoint and editor conflicts
- disposition: extend
- owner: clutch/state.py (export job) using clutch/git.py
- consumers: dispatch eligibility in clutch/drain.py, review pinning of ticket blobs
- observable change: after an accepted revision the exporter writes the exact bytes to the ticket path and commits only that ticket's own `tickets/<stem>/` paths (its `ticket.md` plus any of its changed evidence files, so an intake or authored ticket and its evidence still land in one commit), never another ticket's paths, recording revision, content hash, expected parent and commit SHA. It rechecks the file hash before replacing the file, and refuses and rescans rather than overwriting. An interrupted export is retried idempotently after inspecting HEAD and bytes. A both-changed conflict keeps both versions and holds only that ticket.
- compatibility: `clutch(<stem>)` commits remain the reviewed record. The existing contract that a ticket's evidence is committed together with its ticket (`tests/integration/test_tickets.py::test_bug_evidence_committed_with_ticket`, `tests/integration/test_roadmap_row_author.py`) is preserved unchanged. External edits are detected on startup, on rescan and before export.
- acceptance: a file that changed during export is never overwritten; a crash between database commit and Git commit is repaired on restart with exactly one commit.
- tests: new unit tests using the shared Git fake.
- post-merge source of truth: clutch/state.py

## Scope in / Scope out
Scope in:
- add `clutch/state.py` with the schema, service, endpoint, request-ID idempotency, checkpoint exporter and startup reconciliation;
- port the intake (`clutch/tickets.py::intake`), verdict (`runner.apply_admission`, `Serve.apply_verdict`, `ControlInbox.settle_admissions` consumption) and watcher publication paths onto the service, and delete their former live writers and read paths; `Serve.scan`, `Serve.watch` and verdict settlement must stay free of `DaemonAdmission.exclusive` and `mutations`;
- drain selection and dispatch in `clutch/drain.py` dispatch only revisions whose checkpoint commit exists and skip tickets held for an editor conflict, asking the service for both;
- add `clutch ticket resolve <stem> --keep file|database`, the release path for an editor-conflict hold: it submits through the service, records the chosen version as a new revision on the recorded base, checkpoints it and releases only that ticket's hold; its help, examples and `clutch/docs/host-running.md` verb row ship in the same change;
- update verb help and the docs that describe these commands: the `clutch/docs/host-running.md` verb rows, and `docs/how-clutch-works.md` section 2 and its lock inventory;
- engine-written `# clutch:meta` header lines changed by Check meta fill are in scope and never edited by the implementer;
- update only the one expectation per existing test file listed in the fence that flips because verdict, intake and watcher paths now go through the service.

Scope out:
- merge queue, scheduler sets, holds and pause, service lifecycle, handoff and lock retirement, which remain with `state-merge-queue`, `state-scheduler-sets`, `state-holds-pause` and `state-service-handoff`;
- the journal and its SQL refactor, which stay as they are;
- the evidence-with-ticket commit contract pinned by `tests/integration/test_tickets.py` and `tests/integration/test_roadmap_row_author.py`, which is preserved, not changed;
- the extension JavaScript, which keeps invoking CLI verbs.

The row asks for the smallest deliverable that removes the wait with no dual writer, so it is not split further.

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
- tests/unit/test_state_service.py
- tests/unit/test_state_verdict_no_admission_wait.py
- tests/unit/test_state_checkpoint_conflict.py
- tests/unit/test_drain_checkpoint_dispatch.py
- tests/integration/test_state_endpoint.py
- tests/integration/conftest.py
- tests/unit/test_serve_scan_watch_locks.py
- tests/integration/test_serve_scan_watch_overlap.py
- tests/regress_serve_scan_watch_off_exclusive.py
- tests/unit/test_drain_eligible.py
- tests/unit/test_main_ticket_group.py
- tests/unit/test_main_ticket_verdicts.py

## Acceptance criteria
1. A request replayed with the same request ID returns the recorded result and creates no second revision: `./dev.py test tests/unit/test_state_service.py`.
2. A request with a stale expected revision is refused with a named reason and not applied: `./dev.py test tests/unit/test_state_service.py`.
3. Rows for project A are never returned by a query for project B, and a duplicate or ambiguous registration is refused: `./dev.py test tests/unit/test_state_service.py`.
4. While a run slot is held, `Serve.scan` and verdict settlement both complete and neither enters `DaemonAdmission.exclusive` or `mutations`, and a verdict does not wait on another ticket's held Git or ticket-file serialization (unit file built from fakes, not an integration test): `./dev.py test tests/unit/test_state_verdict_no_admission_wait.py`.
5. A revision is not dispatchable until its checkpoint commit exists, and the commit contains only paths under that ticket's own `tickets/<stem>/` directory (its `ticket.md` plus any of its changed evidence), never another ticket's paths: `./dev.py test tests/unit/test_state_checkpoint_conflict.py`.
6. When both the file and the database changed since the exported base, both versions are kept, the file is not overwritten, that ticket is held, and another ticket still checkpoints: `./dev.py test tests/unit/test_state_checkpoint_conflict.py`.
7. After a simulated crash between the database commit and the Git commit, restart produces exactly one checkpoint commit, not zero or two: `./dev.py test tests/unit/test_state_checkpoint_conflict.py`.
8. With the service unstartable, a verdict verb exits non-zero and leaves the database and the ticket file unchanged: `./dev.py test tests/unit/test_state_service.py`.
9. A real local endpoint round trip authenticates the client and returns the acknowledged result: `./dev.py test tests/integration/test_state_endpoint.py`.
10. No former live writer or read path remains for the ported state, and no SQLite file is opened: `./dev.py test tests/unit/test_state_service.py`.
11. Command help and extension help are consistent with the new and changed verbs: `./dev.py test tests/unit/test_main_help.py tests/unit/test_help.py tests/unit/test_main_ticket_group.py tests/unit/test_main_ticket_verdicts.py`.
12. Drain selection and dispatch skip a revision with no checkpoint commit and a ticket held for an editor conflict, while other tickets still dispatch: `./dev.py test tests/unit/test_drain_checkpoint_dispatch.py`.
13. `clutch ticket resolve <stem> --keep file|database` records the chosen version as a new revision, checkpoints it and releases only that ticket's hold; a ticket that is not held is refused with a named reason: `./dev.py test tests/unit/test_state_checkpoint_conflict.py`.
14. No database transaction is open while a fake Git call, endpoint call or host check is pending: `./dev.py test tests/unit/test_state_service.py`.
15. Dispatch and verdict handling are refused until startup recovery completes, then proceed: `./dev.py test tests/unit/test_state_verdict_no_admission_wait.py`.
16. A ticket edit during a run still invalidates the pinned revision under the ticket-changed contract: `./dev.py test tests/unit/test_state_verdict_no_admission_wait.py`.
17. The exporter rechecks the file hash before replacement and refuses and rescans on change, and an interrupted export retries after inspecting HEAD and bytes: `./dev.py test tests/unit/test_state_checkpoint_conflict.py`.
18. An intake or authored ticket and its changed evidence still land together in one commit: `./dev.py test tests/integration/test_tickets.py tests/integration/test_roadmap_row_author.py`.

## Verification
```
./dev.py test tests/unit tests/integration
```

## Definition of rejected
- A branch that leaves both the old file-based writer and the database writer live for any ported path.
- A branch where a verdict or intake still waits for a held run slot or another ticket's Git work.
- A branch that opens SQLite, or opens DuckDB outside the service.
- A branch that overwrites a ticket file changed by an editor.
- A branch that adds an admission-wide entry for a ported path.
- A branch whose checkpoint commit includes a path outside that ticket's own `tickets/<stem>/` directory.

## Time budget
- expected: 30m
- stuck: 60m
- reason: the row asks for the smallest deliverable that removes the wait with no dual writer, and splitting it would leave a dual writer; the calibration medians are about 6-10m actual per run, so 30m allows for the service, exporter and port together.
````
