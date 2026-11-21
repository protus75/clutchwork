---
state: draft
source: human
priority: P3
kind: chore
---

## Depends on
- spools-capture-keys

## Context
- docs/roadmap.md#6. Owner decisions (decided 2026-11-13)
- clutch/evidence/store.py::capture_key
- clutch/evidence/store.py::CaptureNotFound
- clutch/evidence/store.py::CaptureUnreadable
- clutch/driver.py::Spool
- tests/unit/test_driver_panel_fanout.py
- tests/unit/test_stages_render_check.py
- tests/harness/daemon_soak.py
- tests/waiting.py

## Goal / Why
Roadmap row 189, the helper half of row 63's test split. Row 63 (`spools-onto-evidence-store-r2`) will make `Spool` write through `put_capture(*capture_key(...), data)` and stop writing `spools/`. A test that asserts a `spools/` path would then break, so the tests first reach spool files only through one helper whose body row 63 flips. This ticket creates `tests/spool_captures.py` and routes the unit tests and the daemon soak harness through it. Row 190 (`spools-tests-via-helper`) routes the integration tests. No production file changes; the helper body still reads `<state_dir>/spools/<stem>/<attempt>/<name>` exactly as `Spool.write` writes it, so there is one writer and no dual path.

The helper has three functions, with the signatures row 63 keeps:

- `read_capture(state_dir, spool_stem, attempt, name) -> bytes`: the bytes of the file `Spool.write(spool_stem, attempt, name, text)` wrote under `state_dir / "spools"`.
- `write_capture(state_dir, spool_stem, attempt, name, data) -> None`: writes `data` (`bytes`) to the file `Spool.write(spool_stem, attempt, name, text)` would write under `state_dir / "spools"`, creating the parent directories; for a test that needs a spool file as the input that `harvest` reads. It does no redaction (the data is test input, not a capture).
- `list_captures(state_dir, spool_stem, attempt=None) -> list[tuple[int, str]]`: sorted `(attempt, name)` pairs of the files of one spool slot, for one attempt or, with `attempt=None`, every attempt.

Fields validated, each by `capture_key(spool_stem, attempt, name)` from `clutch/evidence/store.py`, the one owner of the rules, never a copy of them: `spool_stem` is a `str` with at most one `/`, whose part before the `/` fully matches `[a-z0-9][a-z0-9_-]{1,127}` and whose part after it, when present, is `0` or a decimal number without a leading zero of at most 9 digits (`work/1`); `attempt` is an `int`, not a `bool`, at least 0; `name` fully matches `[A-Za-z0-9][A-Za-z0-9._/-]{0,199}`, does not start with `run-<digits>/`, and stays within 200 characters after the `run-<n>/` fold (`check/verify-01.txt`). `state_dir` is a `Path` the caller owns and is not validated. `list_captures` validates `spool_stem` and, when it is not `None`, `attempt`, by the same call with a placeholder name `x`, so a bad listing argument raises the same `ValueError` the store's `captures` raises after the flip.

Named outcomes of `read_capture`:
- `read`: returns the file's bytes unchanged.
- `refused-input`: raises `ValueError` from `capture_key`, before any filesystem access.
- `missing`: raises `CaptureNotFound` when the file does not exist.
- `unreadable`: raises `CaptureUnreadable` when the path exists but cannot be read (a directory, a permission error); the helper catches `OSError` other than `FileNotFoundError` for this.

Named outcomes of `write_capture`:
- `written`: the file exists afterwards with exactly `data`, and `read_capture` returns it; an existing file is overwritten.
- `refused-input`: raises `ValueError` from `capture_key` for an invalid `spool_stem`, `attempt` or `name`, or `TypeError`-free `ValueError` when `data` is not `bytes`, before any filesystem access, so nothing is created.

Named outcomes of `list_captures`:
- `listed`: returns the pairs sorted by attempt number, then name.
- `empty`: returns `[]` when the slot directory is absent or holds no file.
- `refused-input`: raises `ValueError`, as above, before any filesystem access.

What a listing contains is what row 63's store listing would contain, so no caller changes at the flip. The names returned are the names the caller passed to `Spool.write` (`review/m0/call-01/prompt.md`), never with a `run-<n>/` prefix; a spool stem `work/1` lists only the files of that run sequence, and a stem with no `/` lists only files that no run sequence owns. On disk today `Spool` writes `spools/work/1/<attempt>/<name>` for stem `work/1` and `spools/work/<attempt>/<name>` for stem `work`, so `spools/work/1/` holds both attempt 1 of `work` and run 1 of `work/1`. The helper separates them as `capture_key` would: for stem `work/1` only the attempt directories of `spools/work/1/` that are ASCII decimal numbers count (the store's skip rule for attempt directories), and for stem `work` a file whose first path segment under the attempt directory is an ASCII decimal number belongs to a run sequence and is left out.

Files routed through the helper (found by grep for `spools`, `Spool(` and `.spool` over `tests/unit` and `tests/harness`):

- `tests/unit/test_stages_render_check.py` line 93 asserts nothing is written under `spools/work/4/render`: it becomes an assertion that `list_captures(tmp_path, "work", 4)` holds no name starting with `render/`.
- `tests/unit/test_driver_panel_fanout.py` builds `Spool(Path("/spool"), redactor, FakeFileSystem())` and asserts the `prompt.md` paths in the fake filesystem. A fake filesystem cannot be read by the helper, so `rig` takes a `state_dir` (callers pass `tmp_path`) and builds `Spool(state_dir / "spools", redactor, LocalFileSystem())`; the assertion becomes the `list_captures(tmp_path, "item", 1)` names ending in `prompt.md`. That is the one expectation that changes there.
- `tests/unit/test_runner_attempt_manifest.py` line 45 does not assert a spool file: it writes one as the input that `harvest` reads. It calls `write_capture` instead, so row 63's flip, which makes `harvest` read through the store, changes no test file.
- `tests/harness/daemon_soak.py` lines 465, 642 and 671 read `state_dir / "spools/<stem>/<attempt>/<name>"`: each calls `read_capture`. Lines 642 and 671 also test `is_file()`, so the harness gains one module-level function `capture_text(state_dir, stem, attempt, name)` that returns the decoded text, or `None` when `read_capture` raises `CaptureNotFound`; line 465 calls `read_capture` directly, where a missing file should raise.

Files read and left alone, with the reason each is not routed:

- `tests/unit/test_route_kinds_filter.py` and `tests/unit/test_key_scope.py` construct `Spool(tmp_path / "spool", ...)` only to give a `Driver` a writer; neither asserts a spool path, so neither changes.
- `tests/unit/test_projection_leftovers.py` asserts `driver.log._redactor is driver.spool._redactor`, an object identity, not a path.
- `tests/unit/test_evidence_envelope.py` line 219 asserts `spools` is empty after keyless provider calls; it names no stem or attempt and `ProviderLLM` does not use `Spool`, so the helper (which needs a stem) cannot express it. It stays true after the flip (nothing writes `spools/`) but stops proving the point; row 63 owns that line.


## Boundary contract
### Spool capture test helper
- disposition: create
- owner: tests/spool_captures.py
- consumers: `tests/unit/test_driver_panel_fanout.py`, `tests/unit/test_stages_render_check.py`, `tests/harness/daemon_soak.py` and the new `tests/unit/test_spool_captures.py` here; the integration tests of row 190 and the flip of row 63 later
- observable change: the two functions above, with the named outcomes; no production behavior, file, or state changes
- closest existing: `EvidenceStore.get_capture` and `EvidenceStore.captures` read the store, which `Spool` does not write yet, so neither can read what `Spool` writes today; `tests/waiting.py` is the nearest module of shared test support and holds no capture reader
- earning reason: consolidation of evidenced duplicates (three test files and the soak harness hand-build `state_dir / "spools/<stem>/<attempt>/<name>"`) and one body that row 63 flips for every caller at once; key validation reuses `capture_key` rather than a second rule set
- compatibility: new test-support module; the helper's signature is the final one, row 63 changes only its body
- acceptance: criteria 1 to 5 below
- tests: tests/unit/test_spool_captures.py
- post-merge source of truth: tests/spool_captures.py

### Routed spool assertions
- disposition: extend
- owner: the three files in Scope in
- consumers: the unit suite and the soak integration tests
- observable change: each assertion reads spool files through the helper instead of a `spools/` path; `rig` in the panel test writes to a real `tmp_path` instead of a fake filesystem
- compatibility: preserves the asserted facts (which files exist, their text); no assertion weakens
- acceptance: criteria 6 to 8 below
- tests: tests/unit/test_driver_panel_fanout.py, tests/unit/test_stages_render_check.py, tests/integration/test_daemon_soak_runner.py, tests/integration/test_daemon_soak.py
- post-merge source of truth: the same files

## Scope in / Scope out
Scope in:
- New `tests/spool_captures.py` with `read_capture`, `write_capture` and `list_captures` as the Goal states. Both derive the slot directory from the same private function (`state_dir / "spools" / <stem parts> / <attempt>`), so the `spools/` layout is built at one site. The module imports `capture_key`, `CaptureNotFound` and `CaptureUnreadable` from `clutch.evidence.store`, uses `LocalFileSystem` or `pathlib` for reads, and does no I/O at import.
- New `tests/unit/test_spool_captures.py` for the helper, under `tmp_path`, writing its fixtures with the production `Spool` (`clutch.driver.Spool`, a `LocalFileSystem` and `Redactor({})`) so the layout under test is the one `Spool` writes.
- `tests/unit/test_stages_render_check.py`: only the line 93 assertion, plus the import it needs.
- `tests/unit/test_driver_panel_fanout.py`: `rig` gains the `state_dir` parameter and its `Spool`/`LocalFileSystem` construction, the seven `rig(...)` call sites pass `tmp_path` (test functions gain the `tmp_path` fixture), the one `prompt.md` assertion calls the helper, and the `FakeFileSystem` import and the returned `fs` are dropped if nothing else uses them. Nothing else there changes.
- `tests/unit/test_runner_attempt_manifest.py`: only the line 45 write, plus the import it needs.
- `tests/harness/daemon_soak.py`: the three sites above, `capture_text`, and the import. Nothing else there changes.
- The two new `.py` files each start with a `clutch:meta` header with a non-empty one-line `purpose` (write it by hand, or run `uv run clutch meta fill tests/spool_captures.py tests/unit/test_spool_captures.py` and fill an empty purpose), so the meta refresh never renders an empty purpose line. Existing files keep their headers untouched; `tests/unit/test_stages_render_check.py` already reports `drifted` on main before this change, and refreshing headers is the meta tickets' work.

Scope out:
- All production code: `clutch/driver.py`, `clutch/runner.py`, `clutch/evidence/store.py`, every doc and prompt spec. Row 63 flips `Spool` and the helper body.
- Every integration test that asserts a `spools/` path: row 190 (`spools-tests-via-helper`).
- The five files listed under "left alone" in the Goal, and every hot test file the repo conduct file lists (none is edited here).
- Merge order: `index-build-verb-r1` is running and fences the CLI entry module, the run guide, the README, the architecture document and its two index tests, none of which this ticket touches. Confirmed, unmerged tickets that also fence a file edited here (`meta-annotate-tests-unit-a` and `-b`, `training-attempt-manifest`, and the daemon-soak tickets `commit-lock`, `checkpoint-counts-settled`, `active-slot-single-owner`, `closed-sets-single-owner`, `ticket-budget-limits`, `evidence-rusage-capture`, `eval-move-soak-battery-host-loop`, `serve-parallel-dispatch-r2`, `meta-annotate-docs-support`, `integration-test-repo-isolation`) edit header lines or code at other lines of those files; none edits the lines named above, so either merge order leaves both applicable. `spools-onto-evidence-store-r2` fences `tests/spool_captures.py` and depends on this ticket's merge.

## Scope fence
- tests/spool_captures.py
- tests/unit/test_spool_captures.py
- tests/unit/test_driver_panel_fanout.py
- tests/unit/test_stages_render_check.py
- tests/unit/test_runner_attempt_manifest.py
- tests/harness/daemon_soak.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_spool_captures.py` shows `read_capture` returns the exact bytes for a file written by `Spool.write` for stem `my-ticket` attempt 0 and 2, and for stem `work/1` attempt 1 name `check/verify-01.txt`, not `CaptureNotFound`, and that `work/1` and `work/2` with the same attempt and name return different bytes (each reads its own run sequence).
2. The same file shows `read_capture` raises `CaptureNotFound`, not `FileNotFoundError` or `None`, for an absent file, and `CaptureUnreadable`, not `IsADirectoryError`, when the name is a directory.
3. The same file shows `ValueError` from `read_capture` and `list_captures` for stem `""`, `"a/b/c"`, `"Work"`, `None`, `5`; run sequence `"work/01"` and `"work/x"`; attempt `-1`, `True`, `"0"`, `1.0`; name `""`, `"/a"`, `"run-1/a.txt"`; each against a `state_dir` that does not exist, so the failure cannot be a missing directory (the name cases apply to `read_capture` only).
4. The same file shows `list_captures` returns `[(0, "a/x.txt"), (0, "b.txt"), (2, "a/x.txt")]` sorted, not directory order, for one stem with those files; `[]`, not a raise, for a stem with no directory and for a known stem with a different `attempt`; and one pair list for `attempt=2`, not every attempt.
5. The same file shows the folding case: with `Spool` writes for stem `work` attempt 1 name `review/x`, stem `work/1` attempt 0 name `review/call-01/prompt.md` and stem `work/2` attempt 0 name `review/y`, `list_captures(tmp, "work")` is `[(1, "review/x")]`, `list_captures(tmp, "work/1")` is `[(0, "review/call-01/prompt.md")]`, and `list_captures(tmp, "work/2")` is `[(0, "review/y")]`, so no list holds a name starting `run-`.
6. `./dev.py test tests/unit/test_driver_panel_fanout.py tests/unit/test_stages_render_check.py` passes with the panel test asserting the two names `review/m0/call-01/prompt.md` and `review/m1/call-01/prompt.md` from `list_captures(tmp_path, "item", 1)`, not an empty set, and the render test asserting no `render/` name from `list_captures(tmp_path, "work", 4)`.
7. `./dev.py test tests/integration/test_daemon_soak_runner.py tests/integration/test_daemon_soak.py` passes with the harness reading all three sites through the helper.
8. Single call site: `grep -n '"spools' tests/unit/test_driver_panel_fanout.py tests/unit/test_stages_render_check.py tests/harness/daemon_soak.py` prints only the `"spools"` line inside the `Spool(...)` construction in `rig` (the test name `test_member_keys_spools_and_single_member` has no quote before `spools` and does not match), and `grep -n "\"spools\"" tests/spool_captures.py` prints one line (the slot-directory function that both `read_capture` and `list_captures` call), checked in review as a one-time check.
10. `./dev.py test tests/unit/test_spool_captures.py tests/unit/test_runner_attempt_manifest.py` shows `write_capture` then `read_capture` round-trips the exact bytes for stems `my-ticket` and `work/1` (attempts 0 and 1, name `check/verify-01.txt`), that an invalid stem, attempt, name or non-`bytes` data raises `ValueError` and creates no directory under `state_dir`, not a partial file, and that `test_runner_attempt_manifest.py` still passes with its line 45 write going through `write_capture`.
9. `git diff` of the branch shows no file outside the fence changed and no production file under `clutch/` changed, checked in review as a one-time check.

## Verification
```
./dev.py test tests/unit/test_spool_captures.py tests/unit/test_runner_attempt_manifest.py tests/unit/test_driver_panel_fanout.py tests/unit/test_stages_render_check.py tests/integration/test_daemon_soak_runner.py tests/integration/test_daemon_soak.py
uv run ruff format --check .
```

## Definition of rejected
A production file, prompt spec or doc changes; `Spool` or harvest is touched; the helper copies the stem, attempt or name rules instead of calling `capture_key`, or accepts an input `capture_key` refuses; a helper outcome returns a raw `FileNotFoundError` or `None` for a missing file; the `spools/` layout is built at a second site in the helper; `list_captures` returns names with a `run-` prefix or files of another run sequence; an integration test, a file outside the fence, or a hot test file is edited; a routed assertion is weakened or deleted rather than rerouted; the new files lack a `clutch:meta` header or its `purpose` is empty; or a SQLite file is opened.

## Time budget
- expected: 20m
- stuck: 40m
- reason: one helper, its unit test and three small reroutes; the soak tests are the slow part of Verification
