<!-- clutch:meta
schema: clutch.meta/1.0
kind: plan
purpose: Proposed plan to move live engine state into one per-user DuckDB database owned by a single service, removing the DaemonAdmission.exclusive wait, with Git checkpoints, crash recovery, lock retirement and ordered migration tickets
relates: [clutch/rework.py]
owner: clutch/rework.py
verified: 5214eb3e
hash: 412781f2f8f88c92a0d17063023c1a13463d37e85da4ce6a4977f356464ceb59
-->
# Engine state database plan

Status: proposed plan of record, 2026-11-21. The choices below are recommendations for implementation tickets, not shipped behavior.

## 1. Problem

On 2026-11-21 a confirm submitted at 10:58:51Z was applied around 11:05Z when the running ticket merged; `spools-onto-evidence-store-r2` was ready with a disjoint fence but did not start in the interval. `DaemonAdmission.exclusive` waits for all held run slots and prevents new ones while waiting. `Serve.scan` enters it for intake and `Serve.merge` enters it before settling verdicts and processing the merge queue. Shared ticket files and Git's index are the underlying contention, not overlapping implementation fences.

The following inventory describes current sites, not proposed ones. External human/editor writes do not take these locks; intake detects them. The writer rows include the main-checkout paths that motivate the admission boundary.

| File | Function or site | What it protects or writes |
|---|---|---|
| `clutch/lockfile.py` | `Lockfile.acquire`, `release` | Per-checkout `clutch.lock` flock: one engine writer lifetime; released for handoff. |
| `clutch/lockfile.py` | `CommitLock.__aenter__`, `__aexit__` | `commit.lock` flock serializes cooperating Git index/commit operations across processes. |
| `clutch/git.py` | `Git.main_write`, `commit_edit`, `merge_squash` | In-process main-checkout critical section; `commit_edit` and squash also take `CommitLock`. `add`, `commit`, and `restore` take the commit lock. |
| `clutch/daemon.py` | `DaemonAdmission._acquire_run`, `exclusive`, `mutations`, `waiting_for_merge` | Condition bounds run slots and excludes mutations until all slots are lent or released; queued exclusive work blocks new runs. |
| `clutch/daemon.py` | `DaemonCore.startup`, `sweep_orphans` | Exclusive admission around startup recovery and idle orphan sweeping. |
| `clutch/serve.py` | `Serve.scan`, `watch`, `merge` | Admission exclusion around intake, watcher publication/debounce, verdict settlement and merge processing. |
| `clutch/serve.py` | `Serve.run_retro`, `dispatch`, `box_intake`, `maintenance` | Mutation or exclusive admission around retro, supervision, report intake and idle recovery/checkpoint work. |
| `clutch/journal.py` | `Journal.append` | `journal.lock` flock serializes tail repair, roll and durable append. |
| `clutch/journalcache.py` | `open_journal_cache` | Cache flock serializes access to the persistent journal projection. |
| `clutch/scheduler.py` | `Scheduler.dispatch_next` | `_slot` serializes selection and updates of pending/flying dispatch state. |
| `clutch/mergequeue.py` | `MergeQueue` / `process` | `_slot` serializes merge queue processing. |
| `clutch/restart.py` | `Restart` | `_slot` serializes restart/recovery operations. |
| `clutch/stages.py` | `HOST_COMMAND_LOCK`, `run_host_command` | Semaphore serializes host commands such as checks. |
| `clutch/tickets.py` | `intake` | Reads status and validates, stamps and commits pending ticket/evidence paths under both Git locks. |
| `clutch/runner.py` | `verdict_locked`, `reject_ticket`, `apply_admission` | Verdicts and repair stamp ticket files and commit via `commit_edit`; control decisions also journal outcomes. |
| `clutch/daemon.py` | `apply_rework` | Publishes or compensates reviewed ticket proposals through `commit_edit`. `clutch/rework.py::rework` prepares proposals in a workspace, not main. |
| `clutch/author.py` | author publication and decision publication | `commit_edit` publishes ticket proposals and decision records. |
| `clutch/merge.py` | `dirty_overlap`, `write_squash` | Checks checkout overlap under `main_write`; squash and artifact commits use Git serialization. |
| `clutch/roadmap.py` | roadmap publication | Uses `main_write` for main-checkout roadmap edits. |
| `clutch/control.py` | `ControlInbox.settle_admissions`, `write_active` | Consumes verdict requests serially under the engine owner; writes a control projection. Other chats and the extension submit requests or edit files. |

## 2. Proposal

Use one persistent DuckDB database per user, shared by all projects, under the user's Clutch data directory, outside any checkout. A stable project identity identifies the repository across its worktrees; every project-owned row and uniqueness constraint includes that key. Recommend this over one database per project: one service owns one connection and serializes all writes, while explicit keys isolate projects. Registration records canonical repository identity and refuses ambiguous or duplicate registrations rather than silently joining projects.

One long-lived per-user engine service is the sole database writer and owns the connection. It serializes short transactions, never holds one across a model call, host check, Git operation or human wait, and serves concurrent project run workers. Store ticket content and content hashes, revisions and checkpoint status; verdict requests and outcomes; queue order, pending and flying sets; holds and pause state. Use transactions and revision checks for state transitions, idempotency keys for requests, and project-keyed queries throughout. Store enough content, not merely hashes, to export an accepted revision after a crash.

Keep the append-only journal outside as durable history and audit evidence; keep evidence spools and run records as files because they are large artifacts and reviewed run evidence, not mutable scheduling rows. Store references and durable watermarks in the database. Journal and database cannot commit atomically together: use a durable transactional outbox with stable event IDs, append and fsync idempotently, then acknowledge; recovery reconciles both sides before admitting dependent work. This protocol must preserve the journal's existing write-ahead guarantees, including deduplication on a crash after append.

## 3. Command access

Every `clutch` command uses a local authenticated service endpoint for state reads and writes, including commands launched by the VS Code extension and other chats. The extension continues to invoke CLI verbs and render engine snapshots; it never opens the database. Local clients submit project identity, request ID and expected revision, and receive an acknowledged durable result or a specific refusal. Read-only commands use the same service for live state; they do not open DuckDB independently.

The endpoint answers a `ping` request. `clutch engine ping` calls it with a short timeout and exits non-zero if no answer arrives, meaning the engine is hung or dead. This replaces any liveness file; the VS Code extension engine-running indicator uses the verb instead of a file or the writer lock.

If no service runs, a command starts it on demand and waits for recovery and readiness, or reports a clear startup/recovery failure without performing an independent write. A per-user startup ownership lock and endpoint discovery prevent competing services; idle shutdown is allowed only after durable work and checkpoint obligations are settled. Existing long-running serve/drain/run behavior becomes project work hosted by that service. DuckDB's file lock is a last-resort protection against an accidental second opener, not the coordination protocol for clients or multiple writers.

## 4. Git

Ticket files and `clutch(<stem>)` commits remain the reviewed record. The service maintains per-project export jobs: after an accepted ticket or verdict transaction, promptly serialize the exact revision to its ticket path and commit only its paths, using a short project Git/index critical section; never wait for an implementation to finish. Record revision, content hash, expected parent and commit SHA, and do not dispatch a revision until its checkpoint is committed and review pins that blob. Retry an interrupted export idempotently; inspect HEAD and bytes before repeating a commit. Merge and lift remain serialized with export only for their Git operations, not the whole implementation.

Watch and rescan ticket paths, including on startup and before export, so a VS Code edit or another chat's edit is detected even if a notification is missed. Import validates the bytes and compares their hash to the last exported base and current database revision. If only the file changed, import as a new revision, validate and checkpoint it; if only the database changed, export it. If both changed, retain both versions, do not overwrite either, hold that ticket's checkpoint and dispatch, and ask the operator to resolve against the recorded base. An edit during a run still invalidates the pinned ticket revision under the existing ticket-changed contract. A file changing during export is detected by rechecking its hash before replacement; refuse and rescan, not overwrite. Other tickets continue.

## 5. Crash and restart

A transaction acknowledged to a client is durable; an unacknowledged request may or may not have committed, so retry with the same request ID returns its recorded result. On restart the service takes startup ownership, opens and verifies the database, reconciles the journal outbox, Git export jobs and file hashes, then reconstructs worker liveness before admitting work. A dead worker is reconciled from journal and run records rather than treated as still flying; holds and pending requests survive. No acknowledged state is intentionally lost; in-progress model execution can be interrupted, and uncommitted editor buffers are outside engine custody.

If the database is lost or corrupt, quarantine it, rebuild project registrations from an operator-supplied checkout list, import committed ticket files and fold journal events and run records, then rescan uncommitted files. Reconcile unfinished work and request evidence before allowing dispatch. State never checkpointed to files or journal cannot be reconstructed: report the gap and require operator resolution, not fabricate verdicts. Therefore durable request/outbox evidence and checkpoints must precede acknowledgment for state whose loss would be unsafe, and backup of the database remains necessary for data not reconstructible from those records.

Self-upgrade drains or transfers service ownership only after project workers reach a safe handoff, closes the connection and releases the service lock before the replacement opens it; queued durable requests remain available. The current checkout writer lock is retained during migration to protect old paths, then replaced by service ownership and project-scoped Git protection, with no simultaneous old and new writer paths.

## 6. Locks and exclusive sections

Remove `DaemonAdmission.exclusive` as a global wait for running implementations, including its scan, watch and verdict/merge uses, once those mutations are transactional and exports independently serialized. Retain bounded admission slots and a short scheduler transaction for atomic selection; unrelated tickets must continue while an export or verdict is pending. Startup recovery and destructive orphan cleanup still require a project readiness barrier, not a routine all-runs gate.

Retain one per-user service startup/ownership lock, journal append lock while journal writers remain, cache lock while that separate projection exists, project-scoped Git commit/index serialization (including Git's own index lock), merge queue serialization, restart/handoff coordination and host-command semaphore. Their scopes are service ownership, journal integrity, cache integrity, Git's shared checkout/index, ordered merges, recovery and resource contention respectively. Replace `main_write` and `CommitLock` only when every cooperating checkout writer routes through the service's project Git queue; external Git/editor changes still require detection and refusal. Locks are never held across implementation, review or a database transaction waiting for Git.

## 7. Migration

Each row is a proposed small implementation ticket, not an authored ticket. Fences are summaries to rederive against current callers, tests and affected command documentation when authoring. Each step ports its named state and deletes its former live writer/read path in the same change; existing unrelated state remains with its current owner until its own step.

| Order | Stem | Kind | Fence summary | Depends |
|---|---|---|---|---|
| 1 | `state-verdict-ticket-service` | feature | Service, project identity, DuckDB transactions and endpoint with a `ping` handler; `clutch engine ping` with a short timeout, non-zero exit on no answer, help and doc rows; ticket intake, verdict, watcher, admission and Git checkpoint paths; CLI, extension-facing snapshot, tests and affected guides. Establish durable recovery and conflict handling for this slice. Verdict and ticket changes complete while an implementation runs; remove their admission-wide wait. | none |
| 2 | `state-merge-queue` | feature | Merge queue state, Git export coordination, merge/admission consumers and tests; remove the remaining merge-wide implementation wait. | `state-verdict-ticket-service` |
| 3 | `state-scheduler-sets` | feature | Scheduler pending/flying state, selection transactions, recovery and snapshot consumers and tests. | `state-merge-queue` |
| 4 | `state-holds-pause` | feature | Control inbox, holds, pause and their CLI/snapshot consumers, durable outbox and tests. | `state-scheduler-sets` |
| 5 | `state-service-handoff` | feature | Remaining writer routing, service lifecycle, startup, crash rebuild, handoff, lock retirement, extension engine-running indicator switching to `clutch engine ping`, documentation and integration tests. | `state-holds-pause` |

The first slice must include the minimum end-to-end service and checkpoint machinery needed to remove the observed wait, not merely add a database beside the old path. Split its authoring only if the first deliverable still removes that wait without a dual writer. Each slice exercises crash boundaries, cross-project isolation and editor conflicts appropriate to the state moved.

Sequence the deferred `docs/journal-sql-refactor-plan.md` after this migration and its own remeasurement checkpoint. Its journal remains authoritative history and its SQL layer remains a rebuildable read projection; this plan owns live mutable state, not a replacement for journal history. Reassess the deferred plan's connection and cache design after the service lands; do not create a second live-state owner or silently claim its conditional refactor has shipped.

## 8. Open decisions for the owner

1. **Database location:** per user shared across projects or per project? Recommend per user as above, with stable project keys and explicit registration.
2. **Service lifetime:** always-on or on-demand? Recommend on-demand startup with readiness and safe idle shutdown; it supports commands when no engine is running without multiple DuckDB writers.
3. **Concurrent editor conflicts:** automatically merge or preserve both and request resolution? Recommend preserve both and hold only the affected ticket; automatic text merges can change reviewed intent.
4. **Recovery guarantee:** database backups plus journal/files, or make every state change reconstructible from the journal? Recommend durable outbox evidence for acknowledged safety-critical transitions plus backups; report unrecoverable gaps rather than claiming complete reconstruction.
5. **Checkpoint timing:** batch or immediate? Recommend prompt per-revision commits before dispatch, with short serialized Git work; batching can delay review and makes conflict attribution harder.
