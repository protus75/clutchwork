---
state: draft
source: human
priority: P0
kind: feature
---

## Depends on
- none

## Context
- clutch/__main__.py::main
- clutch/__main__.py::_parser
- clutch/lockfile.py::CommitLock
- clutch/docs/host-running.md
- docs/how-clutch-works.md#2. Commands

## Goal / Why
`clutch meta refresh` takes the engine's writer lock ([clutch/__main__.py](clutch/__main__.py) `handle_meta`), so it refuses for as long as a drain or serve runs. All it writes is the metadata header block of named working-tree files; it touches no journal or engine state. On 2026-11-21 that left `docs/roadmap.md` drifted, so the 0.5.0 gate's `meta check` would fail, and the owner couldn't refresh it without stopping the drain. After this ticket `meta refresh` holds only the commit lock, the same lock `ticket review` uses to serialize against the engine's commits and merges. It runs while an engine is live. `meta fill` keeps the writer lock because it makes model calls through a Driver.

## Boundary contract
### meta refresh lock
- disposition: replace
- owner: clutch/__main__.py `handle_meta`
- consumers: operators and agents running `clutch meta refresh`
- observable change: `meta refresh` acquires `CommitLock(config.state_dir, ...)` around its run instead of the writer lock, so it succeeds while another process holds the writer lock and waits (then fails with the existing `CommitLockTimeout` refusal) only while the commit lock is held
- compatibility: `meta fill` still takes the writer lock; `meta check` takes none; refresh output and exit codes are unchanged
- acceptance: criteria 1 and 2
- tests: tests/integration/test_meta_refresh_commit_lock.py
- post-merge source of truth: clutch/__main__.py

## Scope in / Scope out
Scope in:
- clutch/__main__.py `handle_meta`: for `refresh`, wrap `execute()` in `async with CommitLock(config.state_dir, clock=clock, sleep=asyncio.sleep):` instead of `_locked(...)`; `fill` keeps `_locked`. In `_parser`, the meta subcommand help `lock=` text becomes `"Commit lock only."` for refresh, `"Writer lock."` for fill and `"None."` for check.
- clutch/docs/host-running.md `meta refresh` row: change its "Works while serve runs?" cell from `No` to `Yes`, and replace "under the writer lock" with "under the commit lock".
- docs/how-clutch-works.md section 2 `meta refresh [paths]` row: change its lock column from `yes` to `commit only`, matching the `ticket review` row.
- New tests/integration/test_meta_refresh_commit_lock.py.
Scope out:
- `meta fill`, `meta check`, other verbs' locks, and the lockfile module.

## Scope fence
- clutch/__main__.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/integration/test_meta_refresh_commit_lock.py
- tests/unit/test_main_help.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_meta_refresh_commit_lock.py` proves that with the writer lock held by another `Lockfile` holder in the same state dir, `main(["meta", "refresh", <file>])` in a temporary repo exits 0 and rewrites the file's metadata block, not exit 2 with a lock-held refusal.
2. `./dev.py test tests/integration/test_meta_refresh_commit_lock.py` proves that with the writer lock held, `main(["meta", "fill", ...])` still exits 2 naming the lock holder, so fill keeps the writer lock.
3. `./dev.py test tests/unit/test_main_help.py` passes with the per-subcommand lock text.
4. In `clutch/docs/host-running.md` (a one-time review check) the `meta refresh` row reads `| `meta refresh` | Yes | ... under the commit lock. |` and the `meta fill` row is unchanged.

## Verification
```
./dev.py test tests/integration/test_meta_refresh_commit_lock.py tests/unit/test_main_help.py tests/unit/test_meta_fill.py
```

## Definition of rejected
`meta fill` loses the writer lock, refresh runs with no lock at all, or files outside the fence change.

## Time budget
- expected: 10m
- stuck: 20m
