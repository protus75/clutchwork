---
state: draft
source: human
priority: P1
kind: feature
---

## Depends on
none

## Context
- clutch/git.py::Git
- clutch/git.py::Git.merge_squash
- clutch/roadmap.py::_write_row
- clutch/roadmap.py::ship
- clutch/merge.py::dirty_overlap
- tests/unit/test_roadmap_author.py
- tests/unit/test_roadmap_ship.py
- tests/unit/test_merge_dirty.py
- docs/roadmap-driver-plan.md

## Goal / Why
Every write the roadmap driver makes to the main checkout, and every merge admission step that reads or changes that checkout, takes one in-process lock, `Git.main_write()`. Two of them never overlap: a roadmap row edit and its commit (`roadmap._write_row`), a release `roadmap.ship`, the admission's dirty-checkout check (`merge.dirty_overlap`) and the squash (`Git.merge_squash`).

This is the first of three tickets for roadmap row 160, `dispatch-during-driver-pass`: the driver pass will run beside an in-flight ticket (`-drain` for `clutch/drain.py`, then `-serve` for `clutch/serve.py`). Today the pass runs alone between tickets, so nothing contends. Once it overlaps a merge, `_write_row` can leave `docs/roadmap.md` dirty or staged while `dirty_overlap` reads the status, and `ship` can move HEAD under `merge_squash`; the lock removes that race before the overlap lands. The existing `CommitLock` stays: it serializes single git writes across processes, while `main_write` spans a whole read-edit-commit or check-then-squash sequence within one process.

## Boundary contract
### Main-checkout write gate
- disposition: create
- owner: clutch/git.py (`Git.main_write`)
- consumers: `clutch/roadmap.py` (`_write_row`, `ship`) and `clutch/merge.py` (`dirty_overlap`), plus `Git.merge_squash` inside `clutch/git.py`
- observable change: `Git.main_write()` returns the instance's `asyncio.Lock`, used as `async with git.main_write():`. The same lock object is returned on every call. `_write_row` holds it from its fresh read of `docs/roadmap.md` through its commit, `ship` holds it for its whole body, `dirty_overlap` holds it across the status and diff reads, and `merge_squash` holds it around the `merge --squash` and its commit. None of the four calls another of them while holding it, so the lock is never taken twice by one task. Order is `main_write` first, then `CommitLock` inside `git.commit` and `merge_squash`, never the reverse.
- compatibility: no argument, return value, finding or journal event of the four functions changes; a caller that never overlaps another sees no difference
- acceptance: with `main_write()` held by another task, each of the four calls waits and completes after release; an overlapping pair runs strictly one after the other
- tests: new unit test file for the lock and the four callers; three existing fakes gain `main_write`
- post-merge source of truth: clutch/git.py
- closest existing: `Git._commit_lock` (`clutch.lockfile.CommitLock`) in `clutch/git.py`
- earning reason: `CommitLock` is held per git verb, so it cannot cover `_write_row`'s file read, file write and commit, `dirty_overlap`'s two reads, or `ship`'s gate, bump and tag as one sequence; it is also a cross-process file lock whose waits sleep through the clock seam, which an in-process task ordering does not need. Four production consumers across two modules share the one lock.

## Scope in / Scope out
Scope in:
- `clutch/git.py`: add `Git.main_write()` and one `asyncio.Lock` created in `Git.__init__`; wrap the body of `Git.merge_squash` in it, outside the existing `CommitLock`.
- `clutch/roadmap.py`: wrap `_write_row`'s body and `ship`'s body in `async with checkout.git.main_write():`. `drive` and `author_ahead` stay unlocked; they call `_write_row` and `ship`, which lock.
- `clutch/merge.py`: wrap `dirty_overlap`'s body in `async with ctx.git.main_write():`.
- `tests/unit/test_roadmap_author.py`: `FakeGit` gains `main_write` returning a real `asyncio.Lock`; `tests/unit/test_roadmap_accept.py` imports that fake and needs no edit. `tests/unit/test_roadmap_ship.py`: `git=object()` in `test_ship_steps` becomes a namespace with `main_write`. `tests/unit/test_merge_dirty.py`: the `SimpleNamespace` git gains `main_write`. Only those fakes change in these three files.
- A new `tests/unit/test_git_main_write.py` covering the criteria below with fakes and `tmp_path` only.

Scope out: `clutch/drain.py` and `clutch/serve.py` (the `-drain` and `-serve` follow-up tickets move the driver pass off the admission path and use this lock); the roadmap table row 160; `CommitLock`; the window between `dirty_overlap` and `merge_squash` (the lock covers each call, not the pair; a roadmap commit that lands in that window leaves a clean tree, which `merge_squash` squashes onto as today); any other `Git` method. No document describes the lock, so no document changes.

## Scope fence
- clutch/git.py
- clutch/roadmap.py
- clutch/merge.py
- tests/unit/test_roadmap_author.py
- tests/unit/test_roadmap_ship.py
- tests/unit/test_merge_dirty.py
- tests/unit/test_git_main_write.py

## Acceptance criteria
1. `Git.main_write()` returns the same `asyncio.Lock` on every call and a second `Git` instance has its own, checked by `./dev.py test tests/unit/test_git_main_write.py`; a shared module-level lock would fail the second-instance case.
2. While a task holds `git.main_write()`, `Git.merge_squash` issues no `merge --squash` argv until release, and issues it after; checked in `tests/unit/test_git_main_write.py` with a fake process exec, not by timing.
3. While `main_write()` is held, `roadmap._write_row` neither writes `docs/roadmap.md` nor commits until release, so a roadmap file left dirty between its write and commit is never visible to an overlapping `dirty_overlap`; checked in `tests/unit/test_git_main_write.py`, which fails if the lock is removed from `_write_row`.
4. While `main_write()` is held, `roadmap.ship` runs no gate and `merge.dirty_overlap` reads no status until release; each is checked in `tests/unit/test_git_main_write.py`, which fails if either lacks the lock.
5. Two overlapping calls of different holders (`_write_row` with `dirty_overlap`, `ship` with `merge_squash`) run one after the other, never interleaved, and neither deadlocks because none acquires the lock while already holding it; checked in `tests/unit/test_git_main_write.py` with a timeout on each await.
6. Existing results are preserved: `./dev.py test tests/unit/test_roadmap_author.py tests/unit/test_roadmap_accept.py tests/unit/test_roadmap_ship.py tests/unit/test_merge_dirty.py tests/unit/test_git_commit.py tests/unit/test_commit_lock.py` passes.
7. The merge and roadmap integration suites still pass with no edit to them: `./dev.py test tests/integration/test_merge.py tests/integration/test_mergequeue.py tests/integration/test_roadmap_driver.py tests/integration/test_roadmap_ship.py tests/integration/test_serve_admission.py`.

## Verification
```
./dev.py test tests/unit/test_git_main_write.py tests/unit/test_roadmap_author.py tests/unit/test_roadmap_accept.py tests/unit/test_roadmap_ship.py tests/unit/test_merge_dirty.py tests/unit/test_git_commit.py tests/unit/test_commit_lock.py
./dev.py test tests/integration/test_merge.py tests/integration/test_mergequeue.py tests/integration/test_roadmap_driver.py tests/integration/test_roadmap_ship.py tests/integration/test_serve_admission.py
```

## Definition of rejected
The branch takes the lock in `drive`, `author_ahead` or `merge()` instead of the four named functions; any of the four takes `main_write` while already holding it; `main_write` is held inside `CommitLock`; a second lock or a flag is added beside it; `drain.py` or `serve.py` changes; or no test fails when the lock is removed from one of the four callers.

## Time budget
- expected: 20m
- stuck: 40m
- reason: three small code edits and one new test file; not split because the lock and its four callers are one contract
