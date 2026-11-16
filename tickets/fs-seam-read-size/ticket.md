---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- evidence-store

## Context
- clutch/seams.py::FileSystem
- clutch/seams.py::LocalFileSystem
- clutch/evidence/store.py::EvidenceStore
- tests/integration/test_effects.py::FakeFS
- tests/integration/test_effects.py::test_fakes_satisfy_seam_protocols
- tests/unit/test_fs_seam_mkdir_remove.py

## Goal / Why
The `FileSystem` seam in `clutch/seams.py` can list, write, publish, replace, create directories and delete files, but it cannot read a file or report its size. `clutch/evidence/store.py::EvidenceStore` (merged in `evidence-store`) therefore takes two separate callables, `read_bytes(path)` and `size(path)`, for its blob reads, record reads and prune. The next ticket, `evidence-envelope` (roadmap row 29), wires the store into provider calls. A provider client is built on the checkout's `fs`, which is the in-memory `ScriptFS` in the CoreRig tests (`tests/integration/test_daemon_composition.py`). Real file readers there would read or stat paths that exist only in memory and fail on the first prune (the Author decline `tickets/decisions/declined-box-000572-0f2e1a9f.md`). After this change the seam has `read_bytes(path) -> bytes` and `size(path) -> int`, so the store can be given `fs.read_bytes` and `fs.size` and read through the same seam it writes through.

## Scope in / Scope out
Scope in:
- `clutch/seams.py`: the `FileSystem` protocol gains `read_bytes(path) -> bytes` (the file's exact bytes) and `size(path) -> int` (its length in bytes). `LocalFileSystem` implements both with `Path.read_bytes` and `Path.stat().st_size`. Both raise `FileNotFoundError` for an absent path, as `Path` does; neither returns an empty or zero default.
- `tests/integration/test_effects.py`: `FakeFS` gains `read_bytes` and `size`, each raising `AssertionError("not used")` like its `replace` and `publish`, so `test_fakes_satisfy_seam_protocols` keeps passing its `isinstance(fs, FileSystem)` check. This is the only edit in that file.
- New tests in the new file `tests/unit/test_fs_seam_read_size.py`, using only `tmp_path`.

Scope out:
- Any caller of the new methods: `EvidenceStore`, `clutch/providers.py`, `clutch/runner.py` and every other module stay unchanged; `evidence-envelope` adds the callers.
- Other `FileSystem` fakes (`ScriptFS` in `tests/integration/test_daemon_composition.py`, `MemoryFS` in `tests/unit/test_preflight_parallel.py`, and the rest). None is checked against the protocol and nothing calls the new methods on them yet; the ticket that first calls them updates the fakes it reaches.
- The behavior of `mkdir`, `remove`, `entries`, `publish`, `write` and `replace`.

Simpler approach rejected: keeping the store's injected callables and having each caller build real-disk readers is the failure the decline above records; one seam method pair is the minimum that keeps in-memory rigs in memory.

## Scope fence
- clutch/seams.py
- tests/integration/test_effects.py
- tests/unit/test_fs_seam_read_size.py

## Acceptance criteria
1. `tests/unit/test_fs_seam_read_size.py::test_read_bytes_returns_exact_bytes`: after `LocalFileSystem().write(path, b"\x00\xffabc\n")` under `tmp_path`, `read_bytes(path)` returns `b"\x00\xffabc\n"`, a `bytes` value equal to what was written, not a decoded `str`.
2. `tests/unit/test_fs_seam_read_size.py::test_size_counts_bytes`: `size(path)` for that file returns `6`, its byte length, not `0`; for a file holding `"é"` written as UTF-8 it returns `2`, not the character count `1`.
3. `tests/unit/test_fs_seam_read_size.py::test_absent_path_raises`: `read_bytes` and `size` on a path that does not exist under `tmp_path` each raise `FileNotFoundError`; neither returns `b""` or `0`.
4. `tests/unit/test_fs_seam_read_size.py::test_evidence_store_reads_through_the_seam`: an `EvidenceStore(tmp_path, fs, fs.read_bytes, fs.size, lambda s: s)` built on one `LocalFileSystem` returns the original bytes from `get_blob(put_blob(b"payload"))`, and, after an `end.json` holding `{"clock": {"wall_end": "2026-01-01T00:00:00+00:00"}, "raw": {"stdout": <that ref>}}` is published through `fs.publish` under `calls/<key>/`, `prune(0)` removes that blob's file. A `size` that reports `0` leaves the blob in place, so the test fails on it.
5. `tests/integration/test_effects.py::test_fakes_satisfy_seam_protocols` passes, which fails if `FakeFS` lacks `read_bytes` or `size` once the protocol grows them: `./dev.py test tests/integration/test_effects.py`.

## Verification
```
./dev.py test tests/unit/test_fs_seam_read_size.py
./dev.py test tests/integration/test_effects.py tests/integration/test_control.py tests/unit/test_evidence_store.py
```

## Definition of rejected
The branch changes `clutch/evidence/`, `clutch/providers.py`, `clutch/runner.py` or any other caller; gives `read_bytes` or `size` a default for an absent path; changes the behavior of an existing `FileSystem` method; or edits `tests/integration/test_effects.py` beyond `FakeFS`.

## Time budget
- expected: 20m
- stuck: 45m
