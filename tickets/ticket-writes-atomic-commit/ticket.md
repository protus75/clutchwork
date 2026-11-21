---
state: draft
source: human
priority: P0
kind: feature
---

## Depends on
- none

## Runs before
- serve-confirm-during-check
- requisition-review-input-reuse

## Context
- clutch/git.py
- clutch/lockfile.py::CommitLock
- clutch/tickets.py::intake
- clutch/runner.py::verdict_locked
- clutch/runner.py::reject_ticket
- clutch/runner.py::apply_admission
- clutch/author.py::author
- clutch/author.py::commit_record
- clutch/daemon.py::apply_rework
- tests/unit/test_commit_lock.py
- tests/unit/test_verdict_menu_parity.py
- tests/integration/test_author.py
- tickets/serve-verdicts-wait-for-runs/ticket.md
- docs/how-clutch-works.md#10.2 The journal

## Goal / Why
Fix the unsafe ticket write boundary that forces confirmation behind unrelated run lifetimes. The prior serve-verdicts-wait-for-runs ticket was rejected on November 21 because runner, Author and Rework stamp/write ticket files before acquiring the commit lock; adding a Serve-only lock would leave those writers outside it. A scan-trigger patch replaced it, leaving the confirmation barrier intact, and confirmation again waited 183 seconds. Extend the existing Git/commit-lock owner so engine-authored ticket-file edits and their exact-path commits are serialized together. This is orchestration class prevention; the paired serve-confirm-during-check ticket removes the coarse settlement barrier only after these writers are safe. No new Serve-local lock or global run stop is the serialization owner.

## Boundary contract
### Atomic engine ticket edit and commit
- disposition: extend
- owner: clutch/git.py::Git and clutch/lockfile.py::CommitLock
- consumers: confirm/reject, admission replay repair, Author publication/decision records, Rework publication and compensating writes; intake already uses the canonical commit lock
- observable change: add async Git.commit_edit(dir, message, *, only, edit) -> str, where only is a nonempty sequence of exact paths and edit is an async no-argument callback for file reads/writes and read-only Git validation. Acquire Git.main_write first and the existing commit lock second, await edit, then call _commit directly while both remain held. Release on success, exception and cancellation; callbacks never call lock-acquiring Git writers, take either lock recursively, invoke a model or run checks.
- compatibility: preserve existing commit messages, exact-path staging, journal/effect keys, rollback/refusal behavior and CommitLock non-reentrancy. Git.commit remains for already-prepared worktree changes; main ticket writers migrate to the atomic owner, not a parallel unguarded write route.
- acceptance: neither a competing intake nor another state writer observes/stages a stamped file before its owning commit; cancellation leaves the existing replay/refusal contract recoverable and releases ownership
- tests: tests/unit/test_git_commit_edit.py and tests/integration/test_ticket_write_serialization.py
- post-merge source of truth: clutch/git.py::Git.commit_edit and existing commit.lock

## Scope in / Scope out
Scope in:
- Implement the named narrow Git helper with the existing process/filesystem/lock seams. No new lockfile, reentrant lock, transaction journal, worker pool or generic mutation framework. Preserve lock order main_write before commit.lock; never call Git.commit from inside the helper because it acquires the non-reentrant lock again.
- Migrate the actual read/stamp/write plus commit portions of runner.verdict_locked's draft confirmation, runner.reject_ticket, and apply_admission's replay-repair commit. Put state revalidation needed for the edit inside the protected callback, preserving refusal precedence; do not wrap the whole verdict_locked function around intake, since intake already acquires commit.lock.
- The reusable review provenance sibling touches review_candidate and verdict metadata. This ticket changes only final commit() publication closures in Author and publish()/restore_publication() in apply_rework, plus decision-record publication; it leaves review_candidate and every review_ticket/review_with_identity argument and returned provenance untouched. Runs before names the preferred order without depending on that sibling's code; both orders preserve its approval-recording criteria.
- Migrate Author's final ticket write and ticket commit, its decision-record write/commit, and daemon.apply_rework publication and compensation through the same owner. Prepare model output and private evidence before entering; hold no lock across Author/requisition model calls. Preserve existing failure compensation and exact reviewed-byte checks. Read-only preparation is not a replacement for protected final read/validate/write.
- In clutch/tickets.py::intake, wrap its existing entire async with git._commit_lock body in async with git.main_write(), so intake takes main_write then commit.lock around status/read/validation/stamp/_commit. Add an explicit intake-order test in test_ticket_write_serialization.py; preserve the existing commit-lock span. Do not nest the new helper inside intake. Merge squash already takes main_write then commit.lock and remains unchanged.
- Inventory the engine-owned ticket.md stamp/write/commit sites in the run record and name the canonical owner covering each. This is a one-time accounting of these evidenced consumers, not a new lint/enforcement system. Preserve artifact-only writes in independent ticket worktrees.
- In each edit callback, use filesystem reads/writes/removes and read-only _run/rev_parse only. In daemon.apply_rework compensation, replace the existing add/restore/commit sequence with commit_edit whose callback restores pre-publication bytes (or removes an owned new file) after checking current bytes still equal this publication's output; do not call add, restore or commit inside the callback. Ignore only NothingToCommit when restoration leaves no Git delta. Preserve another writer's later bytes rather than undo them. Author failure compensation follows the same owner and owned-byte check. Add test_callback_never_reenters_writer_lock to test_ticket_write_consumers.py using a non-reentrant fake lock that raises on recursive acquire, exercising success, partial publication and compensation.
- Unit tests use in-memory fake lock objects, fake process exec and injected filesystem operations or tmp_path, not real fcntl or repository files. Real flock, real Git and committed-fixture races belong only in tests/integration/test_ticket_write_serialization.py.
- Add event-controlled fake-driven unit tests exercising the helper and migrated consumer branches; integration tests race intake and confirm/reject/Author/Rework writes and assert exact committed bytes, no adoption of another writer's intermediate stamp, lock release on failure, and unchanged request replay.
- Migrate the hand-built Git fixture in test_verdict_menu_parity.py to implement commit_edit explicitly; preserve its verdict admission expectations. Update the commit-failure interception in test_author.py to exercise the new protected commit path, retaining its existing compensation assertions. Migrate the same reaching Git stand-ins in tests/unit/test_author_roadmap_row.py and tests/unit/test_key_scope.py. Update the Rework commit-failure hooks in tests/integration/test_ladder.py, test_drain.py and test_daemon_composition.py to intercept commit_edit/_commit as appropriate, preserving the existing partial-publication/refusal assertions. In those two hot files change only the forced existing failure hooks; add no test, fixture or helper there. tests/integration/test_stages.py:768 intercepts artifact checks commits, not migrated ticket.md writes, and remains unchanged. tests/unit/test_commit_lock.py::test_git_holds_one_lock_per_write still calls unchanged commit, merge_squash, add and restore methods and remains unchanged; new helper assertions live in the new unit file. Adjust other listed verdict fakes only where they reach the new method; add no getattr fallback or default fake method to production.
- Document the narrow ticket-write critical section in how-clutch-works and the Git helper docstring. Leave serve's coarse run exclusion unchanged here; its removal is the paired instance ticket's deliverable.
Scope out:
- No change to scheduler parallelism, merge code, provider routing, user-authored file editing, command semantics, engine lifetime locks, lock timeouts, or the pending review-policy tickets' goals. Preserve the approved pending reuse ticket's identity wrapper when touching Author/Rework publication.

## Scope fence
- clutch/git.py
- clutch/tickets.py
- clutch/runner.py
- clutch/author.py
- clutch/daemon.py
- docs/how-clutch-works.md
- tests/unit/test_git_commit_edit.py
- tests/unit/test_ticket_write_consumers.py
- tests/integration/test_ticket_write_serialization.py
- tests/unit/test_verdict_menu_parity.py
- tests/unit/test_verdict_extension.py
- tests/unit/test_reject_reason_paths.py
- tests/integration/test_author.py

- tests/unit/test_author_roadmap_row.py
- tests/unit/test_key_scope.py
- tests/integration/test_ladder.py
- tests/integration/test_drain.py
- tests/integration/test_daemon_composition.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_git_commit_edit.py` proves edit precedes exact-path _commit while main_write and commit.lock are held, competing tasks are excluded, lock order is fixed, and exceptions/cancellation release both locks without making CommitLock reentrant.
2. `./dev.py test tests/unit/test_ticket_write_consumers.py tests/integration/test_ticket_write_serialization.py` proves all named state-changing consumers protect their final file mutation and commit through the same owner; intake cannot commit another writer's intermediate stamp, and a later legitimate state edit is not overwritten by failure compensation.
3. `./dev.py test tests/unit/test_verdict_menu_parity.py tests/unit/test_verdict_extension.py tests/unit/test_reject_reason_paths.py tests/integration/test_author.py` preserves verdict/refusal/reason forwarding, recovery and publication-failure behavior through the migrated API.
4. `./dev.py test tests/integration/test_ticket_write_serialization.py` proves model/check work runs outside the narrow write lock and existing merge squash/commit-lock serialization is preserved; there is no new run-lifetime lock.

## Verification
```
./dev.py test tests/unit/test_git_commit_edit.py tests/unit/test_ticket_write_consumers.py tests/integration/test_ticket_write_serialization.py tests/unit/test_commit_lock.py tests/unit/test_verdict_menu_parity.py tests/unit/test_verdict_extension.py tests/unit/test_reject_reason_paths.py tests/integration/test_author.py tests/unit/test_author_roadmap_row.py tests/unit/test_key_scope.py tests/integration/test_ladder.py tests/integration/test_drain.py tests/integration/test_daemon_composition.py
```

## Definition of rejected
A new Serve-only lock substitutes for migration of the real writers; any named engine ticket state writer still changes bytes before obtaining shared ownership; locks span a model/test run, recursive commit-lock acquisition is introduced, unrelated user changes are staged, or compensation overwrites another completed edit.

## Time budget
- expected: 30m
- stuck: 60m
