---
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
source: box:roadmap_row
state: confirmed
---

## Depends on
none

## Context
- clutch/seams.py::FileSystem
- clutch/seams.py::LocalFileSystem
- clutch/enginelog.py
- clutch/journal.py::Journal.__init__
- tests/integration/test_effects.py

## On-demand
- clutch/stages.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_restart_timers.py

## Goal / Why
The `FileSystem` seam in `clutch/seams.py` has `entries`, `publish`, `write` and `replace` but no way to create a directory or delete a file. Engine code therefore calls `Path.mkdir` and `Path.unlink` directly, which the repo's seam rule ("Use the injectable seams") forbids and which fake-driven tests cannot observe. After this change the seam has `mkdir` and `remove`, and `enginelog`, `journal` and `stages` use them instead of raw `Path` calls. The planned evidence store needs both methods on the seam.

## Scope in / Scope out
In:
- `FileSystem` protocol gains `mkdir(path)` (create the directory and any missing parents; an existing directory is not an error) and `remove(path)` (delete a file; an absent path is not an error). `LocalFileSystem` implements both with `Path.mkdir(parents=True, exist_ok=True)` and `Path.unlink(missing_ok=True)`.
- `clutch/enginelog.py`: `EngineLog.event` creates its directory through a `LocalFileSystem` held on the instance, as `Journal` already holds one. The `EngineLog` constructor signature does not change, so its twelve construction sites stay untouched.
- `clutch/journal.py`: `Journal.append` creates `self.dir.parent` with `self._fs.mkdir`.
- `clutch/stages.py`: each `path.parent.mkdir(...)` in the worktree helpers and each `.unlink(...)` (lift_outbox, the Check outbox cleanup, the host-check results cleanup, the base-worktree results cleanup, and the invalid-artifact cleanup) becomes `ctx.fs.mkdir` / `ctx.fs.remove`. Every one of these callers already tolerates an absent file or is guarded by the file existing, so the idempotent `remove` is safe.
- Test doubles that must satisfy the protocol: `FakeFS` in `tests/integration/test_effects.py` gains `mkdir` and `remove` (it is checked with `isinstance(fs, FileSystem)`); `ScriptFS` in `tests/integration/test_daemon_composition.py` gains `mkdir` (no-op) and `remove` (`self.files.pop(path, None)`). These are the only edits in those two files.
- `tests/integration/test_restart_timers.py`: the `repository` fixture (line 96) already patches `rig.fs.write` so each write calls the `ScriptFS` method and then `LocalFileSystem.write`. It gains the same mirror for `rig.fs.mkdir` and `rig.fs.remove`: call the `ScriptFS` method, then the `LocalFileSystem` one. Without this, stage cleanup through `ctx.fs.remove` leaves real outbox files on disk and the fixture's callers (such as `tests/integration/test_serve_admission.py`) fail. This is the only edit in that file.
- New tests in new files only (see fence).

Out:
- `clutch/driver.py` and `scheduler.write_queue` (`clutch/drain.py::write_queue`): neither calls `mkdir` or `unlink`. They already write through `fs.write`, which creates parent directories inside `LocalFileSystem`. They need no change, and this ticket does not touch them.
- `LocalFileSystem.publish` and `write` keep their own internal `mkdir` calls; `seams.py` is the seam implementation itself.
- No change to the `entries`, `publish`, `write` or `replace` behavior, no new flags, no other modules.

Simpler approach rejected: threading an `fs` argument through `EngineLog`'s constructor would touch twelve call sites for no behavior gain; holding a `LocalFileSystem` on the instance mirrors `Journal` and is the minimum.

## Scope fence
- clutch/seams.py
- clutch/enginelog.py
- clutch/journal.py
- clutch/stages.py
- tests/integration/test_effects.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_restart_timers.py
- tests/unit/test_fs_seam_mkdir_remove.py
- tests/integration/test_fs_seam_sites.py

## Acceptance criteria
1. `tests/unit/test_fs_seam_mkdir_remove.py::test_mkdir_creates_parents_and_is_idempotent`: `LocalFileSystem().mkdir(tmp_path / "a" / "b")` creates the nested directory, and a second call on the same path returns without raising `FileExistsError`.
2. `tests/unit/test_fs_seam_mkdir_remove.py::test_remove_deletes_file_and_tolerates_absent`: after `remove` the file no longer exists (`not path.exists()`), and `remove` on a path that never existed returns `None` without raising `FileNotFoundError`.
3. `tests/unit/test_fs_seam_mkdir_remove.py::test_enginelog_creates_missing_directory`: `EngineLog(tmp_path / "deep" / "engine.log", ...)` with a fake clock writes one event and the file exists with one line; the missing `deep` directory was created.
4. `tests/unit/test_fs_seam_mkdir_remove.py::test_journal_append_creates_state_dir`: `Journal(tmp_path / "state", clock).append(...)` on a nonexistent state dir succeeds and `journal.read()` returns that one event, not an empty list.
5. `tests/integration/test_fs_seam_sites.py::test_no_raw_path_mkdir_or_unlink_in_seam_users`: an `ast` scan of `clutch/enginelog.py`, `clutch/journal.py` and `clutch/stages.py` finds zero calls whose attribute name is `unlink`, and every call whose attribute name is `mkdir` has as its receiver an Attribute whose attr is `fs` or `_fs` (the fs seam, such as `self._fs` or `ctx.fs`); the wrong result it rules out is a `mkdir` call on any other receiver or any `unlink` call.
6. `tests/integration/test_effects.py::test_fakes_satisfy_seam_protocols` still passes, which fails if `FakeFS` lacks `mkdir` or `remove` once the protocol grows them.
7. `./dev.py test tests/integration/` passes in full (this includes `test_stages.py`, `test_daemon_composition.py`, `test_journal.py`, `test_driver.py`, `test_restart_timers.py` and the `repository` fixture's callers such as `test_serve_admission.py`), with no test edited beyond those named in Scope in.

## Verification
```
./dev.py test tests/unit/test_fs_seam_mkdir_remove.py tests/integration/test_fs_seam_sites.py tests/integration/test_effects.py
./dev.py test tests/integration/
```

## Definition of rejected
The branch adds an `fs` parameter or any other knob to `EngineLog`, leaves a `.mkdir(` or `.unlink(` call on a Path rather than the fs seam in `enginelog.py`, `journal.py` or `stages.py`, changes `driver.py` or `drain.py`, changes the behavior of `publish`, `write`, `replace` or `entries`, edits `test_restart_timers.py` beyond the `repository` fixture's mkdir/remove mirror, or adds tests to an existing hot test file.

## Time budget
- expected: 30m
- stuck: 60m