---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
none

## Context
- docs/journal-sql-refactor-plan.md
- clutch/daemon.py::DaemonAdmission
- clutch/serve.py::Serve.scan
- clutch/serve.py::Serve.merge
- clutch/lockfile.py::CommitLock
- clutch/git.py
- docs/parallel-tickets-plan.md

## Goal / Why
Serve runs one ticket at a time for much of the time even with `scheduler.parallel` `max_runs` 2. On 2026-11-21 a confirm submitted at 10:58:51Z was applied only at 11:05Z, when the one running ticket merged, and no second ticket started in between although `spools-onto-evidence-store-r2` was ready with a disjoint fence. The cause is the exclusive admission section (`DaemonAdmission.exclusive`, taken by `Serve.scan` and `Serve.merge`): every ticket-file change and every verdict waits for all running implementations, and while it waits serve starts nothing. The section exists because several writers (the owner, other chats, the supervisor, intake, the merge queue) edit ticket files in the main checkout and commit them, and git has one index. The owner wants the locking design replaced, not patched again (`box-000916`, `box-000933`, ticket `serve-scan-ignores-head-moves` each moved one trigger and left the design).

After this ticket `docs/engine-state-db-plan.md` exists and is the plan of record for moving live engine state (the queue, ticket and verdict state, the scheduler's pending and flying sets, hold and pause state) into one DuckDB database that every `clutch` command reaches through the engine, so concurrent writers take transactions instead of an exclusive section, with files and git commits written from the database at checkpoints. One database serves every project that uses clutch. No code changes in this ticket.

## Boundary contract
### Engine state plan
- disposition: create
- owner: docs/engine-state-db-plan.md
- consumers: the owner, ticket authors for the plan's implementation tickets, and the journal SQL plan, which it must reconcile with
- observable change: a new plan document; no behavior change
- compatibility: no code, config, ticket or other document changes except the plan's own `clutch:meta` header
- acceptance: criteria 1 to 3
- tests: none; the plan is verified in review, and a standing test pinning its text is not added
- post-merge source of truth: docs/engine-state-db-plan.md
- closest existing: the journal SQL plan (journal reads only, deferred) and the parallel tickets plan (the scheduler, not the state store)
- earning reason: neither covers writes, ticket and queue state, git export, or multiple projects; extending the journal plan would turn a read optimization into a storage redesign

## Scope in / Scope out
Scope in: write `docs/engine-state-db-plan.md` with these sections, then `uv run clutch meta refresh docs/engine-state-db-plan.md` with only `purpose` edited by hand. The implementer reads `clutch/daemon.py`, `clutch/serve.py`, `clutch/git.py`, `clutch/runner.py`, `clutch/rework.py`, `clutch/control.py`, `clutch/journal.py`, `clutch/tickets.py`, `clutch/lockfile.py` and the engine overview before writing and cites real function names; no claim about the code is written from memory.
1. Problem: the evidence above; a table of every lock, exclusive section and main-checkout writer found today (file, function, what it protects), from reading the code.
2. Proposal: one DuckDB database, its location (per user, shared by all projects, with a project key on every row, versus per project; recommend one and say why), what lives in it (queue, ticket state and content hashes, verdict requests, scheduler sets, holds), what stays outside it (the append-only journal, evidence spools, run records) and why, and the single process that owns writes.
3. How every `clutch` command, the VS Code extension and other chats reach it: through the engine process, with the behavior when no engine runs. Say whether DuckDB's own file locking is relied on.
4. Git: ticket files and `clutch(<stem>)` commits remain the reviewed record. State when and how the database is checkpointed to files and commits (who commits, how a human edit of a ticket file in VS Code is detected and imported, how conflicts between a file edit and a database change resolve).
5. Crash and restart: recovery, what a crash can lose, and how the database is rebuilt from files and the journal; relation to the existing handoff and writer lock.
6. Which of today's locks and exclusive sections go away, which stay (for example git's own index lock at commit time), and what each remaining one protects.
7. Migration: an ordered list of small tickets (stem, kind, fence summary, depends) that moves one state kind at a time with no dual path left behind, starting with the verdict and ticket-file path that causes the delay; and how it reconciles with the journal SQL plan (supersede, merge, or sequence).
8. Open decisions for the owner, each with options and a recommendation.

Scope out: any code, test, config, roadmap row or ticket; the engine overview; the journal SQL plan's own text.

## Scope fence
- docs/engine-state-db-plan.md

## Acceptance criteria
1. `docs/engine-state-db-plan.md` has the eight sections named in Scope in as `##` headings, and its lock table names at least the sites in `clutch/daemon.py` (`DaemonAdmission`), `clutch/serve.py` (`Serve.scan`, `Serve.merge`) and `clutch/lockfile.py` (`CommitLock`) and `clutch/git.py` (`main_write`), each with the file and function it was read from.
2. `docs/engine-state-db-plan.md` section 7 lists the implementation tickets in order, each with a stem, kind, fence summary and depends, and its first entry removes the wait of a verdict or ticket-file change on a running implementation.
3. `uv run clutch meta check docs/engine-state-db-plan.md` exits 0, and `git diff --name-only main` lists only `docs/engine-state-db-plan.md`.

## Verification
```
uv run clutch meta check docs/engine-state-db-plan.md
```

## Definition of rejected
A plan that keeps the exclusive section and adds another lock beside it; a plan section written without reading the code it describes; any code, config, test, roadmap or other document changed; a lock table with a site that does not exist.

## Time budget
- expected: 25m
- stuck: 50m
