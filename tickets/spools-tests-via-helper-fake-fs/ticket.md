---
state: confirmed
source: human
priority: P3
kind: chore
---

## Depends on
- spools-test-helper

## Context
- tests/spool_captures.py
- tests/unit/test_spool_captures.py
- clutch/seams.py::FileSystem
- tests/fakes.py::FakeFileSystem
- clutch/evidence/store.py::capture_key
- clutch/evidence/store.py::EvidenceStore.__init__
- tests/integration/test_watchdog_activation.py::test_every_production_driver_surface_is_watched
- tests/integration/test_watchdog_activation.py::test_eval_owned_budgets_preserve_synthetic_identities
- tests/integration/test_watchdog_activation.py::test_production_hard_timeout_group_kill_is_harvested
- tests/integration/test_provider_cooldown_failover.py::test_mid_run_drought_is_harvested_without_spine_draws
- tickets/spools-test-helper/ticket.md
- tickets/spools-tests-via-helper/ticket.md
- tickets/spools-onto-evidence-store-r2/ticket.md

## Goal / Why
Roadmap row 195, part 3 of 3 of row 63's test split (parts 1 and 2 are rows 190 and 194). Row 63 (`spools-onto-evidence-store-r2`) flips the body of the helper `tests/spool_captures.py` to read through `EvidenceStore` and `capture_key`, and every test must already reach spool files through that helper. Two integration tests cannot: `tests/integration/test_watchdog_activation.py` (3 sites in the `FakeFileSystem` dictionary `rig.fs.files`, plus 1 real-disk glob) and `tests/integration/test_provider_cooldown_failover.py` (1 site) assert a `spools/` path inside `rig.fs.files`, and the helper reads `<state_dir>/spools/` with `pathlib`, so it cannot see a fake filesystem.

After this ticket, `read_capture`, `write_capture` and `list_captures` take an optional keyword-only parameter `fs`. Omitted (or `None`) they behave exactly as today on the real disk. Given a `FileSystem` seam object (`clutch/seams.py::FileSystem`; the tests pass the `FakeFileSystem` of `tests/fakes.py`) they read and write through it, with the same `capture_key` validation and the same outcomes. The two tests then call the helper with `fs=rig.fs` and build no `spools/` path.

How row 63's flip honors `fs`: `EvidenceStore.__init__` takes `(state_dir, fs, read_bytes, size, redact)`. The flipped helper builds the store with `fs` when given, else a `LocalFileSystem()`, and passes `fs.read_bytes` and `fs.size`. The `fs` keyword stays in the signature and means "the filesystem the store sits on", so no caller changes at the flip.

Seam facts read before writing this ticket: `FileSystem` has `mkdir`, `remove`, `entries` (sorted names directly inside a directory, empty list if absent), `publish`, `write` (creates parents), `replace`, `read_bytes` and `size`. It has no `is_dir`, `exists` or recursive listing. `FakeFileSystem.read_bytes` raises `FileNotFoundError` for a missing path and also for a directory path (a directory is not a key of its `files` dictionary); `LocalFileSystem.read_bytes` raises `IsADirectoryError` for a directory. `LocalFileSystem.entries` raises `NotADirectoryError` for a file.

The call sites, with the stem, attempt and name each old path spells (verified in `clutch/driver.py`: the spool stem is `f"{stem}/{run_seq}"` when a run sequence exists, else `stem`, and the name is `<surface>/call-NN/prompt.md` or `output.txt`):

- `test_watchdog_activation.py` line 161: `spools/author/8/0/requisition_review/call-01/prompt.md` is stem `"author/8"` (run sequence 8), attempt `0`, name `requisition_review/call-01/prompt.md`.
- line 307: `spools/baseline-{fixture.name}/{attempt}/review/call-01/prompt.md` is stem `f"baseline-{fixture.name}"`, attempt `attempt`, name `review/call-01/prompt.md`.
- line 335: `spools/diagnose-eval-{case.name}/1/diagnose/call-01/prompt.md` is stem `f"diagnose-eval-{case.name}"`, attempt `1`, name `diagnose/call-01/prompt.md`.
- line 461 (`test_production_hard_timeout_group_kill_is_harvested`): `assert not list(ctx.config.state_dir.glob("spools/work/**/output.txt"))` reads the real disk, while the driver spool writes through `ctx.fs`; the helper with `fs=ctx.fs` is the faithful read. It becomes an assertion over stem `"work"`, attempt `0` (a ticket run carries no run sequence, so `clutch/driver.py` spools it under the plain ticket stem: `spools/work/0/implement/call-01/prompt.md`), with a positive control so it cannot pass on an empty listing: the listing for stem `"work"`, attempt `0` holds the `prompt.md` capture the run did write (a listing of `[]` fails), and no listed name ends with `output.txt`. Check first that `ctx.fs` is the filesystem the driver's spool writes to (`test_daemon_composition.py` asserts `ctx.driver.spool._fs is ctx.fs`); if it is not, pass the filesystem the spool holds.
- `test_provider_cooldown_failover.py` line 267: `rig.fs.files[state_dir / "spools/midrun/0/implement/call-01/output.txt"].decode()` is stem `"midrun"`, attempt `0`, name `implement/call-01/output.txt`, a text read.

Existence sites (161, 307, 335) keep their fact "the file exists" as `(attempt, name) in list_captures(state_dir, stem, fs=rig.fs)`, which does not require the prompt text to be non-empty. Fixture and case names (`accept-slugify`, `escalate_algorithm`) were checked against the stem rule and are valid.

A grep of `tests/` for `fs.files` next to `spools` finds exactly these two files and no other test, so the fence is closed.

## Boundary contract
### Spool capture test helper filesystem parameter
- disposition: extend
- owner: tests/spool_captures.py
- consumers: `tests/unit/test_spool_captures.py`, `tests/integration/test_watchdog_activation.py`, `tests/integration/test_provider_cooldown_failover.py`, and at the flip `spools-onto-evidence-store-r2`
- observable change: the three functions accept `fs=None` as a keyword-only parameter; with a `FileSystem` object they read, write and list through it; with `None` nothing changes
- compatibility: every existing call (positional state_dir, spool_stem, attempt, name, data) keeps its result, its exceptions and its disk effects; the existing unit tests pass unedited
- acceptance: criteria 1 to 6 below
- tests: tests/unit/test_spool_captures.py and the two integration tests
- post-merge source of truth: tests/spool_captures.py for the `spools/<stem>/<attempt>/<name>` layout and the `fs` parameter; `clutch/seams.py::FileSystem` for the seam

## Scope in / Scope out
Scope in:
- `tests/spool_captures.py`: add `fs=None`, keyword-only, to `read_capture`, `write_capture` and `list_captures`. Rules per field:
  - `state_dir`: a `Path`; the layout is `state_dir / "spools" / <stem> / <attempt> / <name>`, with or without `fs`. Not validated beyond what `capture_key` does for the other fields (unchanged).
  - `spool_stem`, `attempt`, `name`: validated by `capture_key` exactly as today, before any filesystem access, with or without `fs`. Invalid values raise `ValueError` and leave the fake's `files` and `directories` untouched.
  - `data` (`write_capture`): must be `bytes`, else `ValueError`, with or without `fs`.
  - `fs`: `None` (the default) means the real disk through `pathlib`, the code path that exists today, left untouched. Anything else is used as a `FileSystem` seam object and is not type-checked: it must provide `read_bytes`, `write` and `entries`, and an object lacking one raises `AttributeError` from the call, not a helper error. `fs=LocalFileSystem()` on a real directory gives the same results as the default.
  - `read_capture` with `fs`: `fs.read_bytes(path)`. `FileNotFoundError` raises `CaptureNotFound(str(path))`; any other `OSError` raises `CaptureUnreadable(str(path))`; the same two outcomes as the real-disk path. A directory path in a `FakeFileSystem` raises `CaptureNotFound` (the fake reports it as missing); that is the fake's behavior and is not special-cased.
  - `write_capture` with `fs`: `fs.write(path, data)` (the seam creates parent directories and replaces an existing file). Returns `None`.
  - `list_captures` with `fs`: walks `state_dir / "spools" / <stem>` with `fs.entries`. A directory under it whose name is ASCII decimal is an attempt; with `attempt` given only that attempt is listed. Inside an attempt, an entry whose `entries` call returns names is a directory and is walked; an entry with no children (or whose `entries` call raises `NotADirectoryError`) is a file only if `fs.read_bytes(path)` succeeds, and is skipped on an `OSError` (an empty directory). Absent root returns `[]`. The result is the sorted list of `(attempt, name)` with `/`-separated names, filtered by the same rules as the real-disk branch: skip a name that fails `capture_key(spool_stem, attempt, name)` and, for a stem without `/`, skip a first path segment that is ASCII decimal (a run directory of stem `work/<n>`). Share that filter between the two branches in one private function; do not copy it.
  - Do not add a parameter other than `fs`, and do not change a signature otherwise.
- `tests/unit/test_spool_captures.py`: append tests using `FakeFileSystem` from `tests/fakes.py` and `Spool(Path, Redactor({}), fake)` as the production writer. The existing tests are not edited. The tests cover: round trip of `write_capture` then `read_capture` with `fs`, including the key landing at `state_dir/"spools"/stem/str(attempt)/name` in `fake.files` and bytes returned unchanged; overwrite; a missing file raises `CaptureNotFound`; the invalid stem, attempt, name and non-bytes data cases raise `ValueError` with `fs` and leave `fake.files` and `fake.directories` empty; listing with `fs` equals the listing of the same writes on a real `tmp_path` (the same data as `test_listing` and `test_listing_overlapping_runs`, including a `run-1/invalid` name, a `bad name`, an empty directory made with `fake.mkdir`, a second attempt, and an `attempt` filter); `fs=LocalFileSystem()` equals the default on a real directory.
- `tests/integration/test_watchdog_activation.py` and `tests/integration/test_provider_cooldown_failover.py`: route the five sites in Goal through the helper with `fs`, plus the import each file needs (`from tests.spool_captures import list_captures, read_capture`). Nothing else in those files changes. The two files already carry a clutch meta header; leave it untouched (the repo's own meta rules for existing headers are not this ticket's concern).
- This ticket creates no new Python file, so no new meta header is needed.

Scope out:
- All production code, docs, prompt specs, and the flip itself (row 63, `spools-onto-evidence-store-r2`, rewrites the helper body and keeps `fs`).
- The driver family (`spools-tests-via-helper-driver`, row 194) and the merge family (`spools-tests-via-helper`).
- Any other filesystem method added to the seam, and any change to `tests/fakes.py`.
- Merge order: the confirmed tickets that fence the two integration files (for example `requisition-prior-required`, `move-serve-rig`, `meta-annotate-tests-integration-b`) edit other lines or the file header; this ticket edits only the five assertion lines and the import block, so either order merges. If another ticket has already moved or renamed a test function named in Context, the implementer follows the assertion, not the function name.

## Scope fence
- tests/spool_captures.py
- tests/unit/test_spool_captures.py
- tests/integration/test_watchdog_activation.py
- tests/integration/test_provider_cooldown_failover.py

## Acceptance criteria
1. Single call site: `grep -n 'spools' tests/integration/test_watchdog_activation.py tests/integration/test_provider_cooldown_failover.py` prints no line, not a `spools/` literal left in either file.
2. `./dev.py test tests/unit/test_spool_captures.py` passes with every test that existed before this ticket unedited (`git diff` of that file shows only added lines), so the real-disk default behaves exactly as before.
3. New unit tests pass: with `fs=FakeFileSystem()`, `read_capture` of an absent file raises `CaptureNotFound`, not `CaptureUnreadable` and not `FileNotFoundError`; an invalid stem, attempt or name raises `ValueError` and `fake.files` stays `{}`; `write_capture(..., "text")` with `fs` raises `ValueError`, not stores text; and the listing with `fs` equals the real-disk listing for the same writes, so a helper that returned `[]` for the fake fails.
4. `./dev.py test tests/integration/test_watchdog_activation.py tests/integration/test_provider_cooldown_failover.py` passes, with the line-461 site asserting a `prompt.md` capture IS present in the listing for stem `"work"`, attempt `0` (the stem a ticket run really uses; a listing of `[]` fails the positive control) and that no listed name ends with `output.txt`, and with the three existence sites still asserting presence of the prompt capture for the stems `"author/8"`, `baseline-<fixture>` and `diagnose-eval-<case>` (membership in `list_captures`, never an assertion that is true for an empty listing), the cooldown site still asserting `"earlier evidence"` in the decoded `midrun` output text.
5. The signature of each of the three functions differs from today only by `*, fs=None` (`inspect.signature` in review, one-time check), and `git diff --stat` shows no file outside the fence and no file under `clutch/` changed.
6. A site that routes the helper through `fs` fails when the file is absent: temporarily asserting a name that was never written (for example `implement/call-99/output.txt` for `midrun`) raises `CaptureNotFound` through the cooldown call, checked once in review, not left in the file.

## Verification
```
./dev.py test tests/unit/test_spool_captures.py tests/integration/test_watchdog_activation.py tests/integration/test_provider_cooldown_failover.py
uv run ruff format --check tests/spool_captures.py tests/unit/test_spool_captures.py tests/integration/test_watchdog_activation.py tests/integration/test_provider_cooldown_failover.py
```

## Definition of rejected
A production file, doc, `tests/fakes.py` or a file outside the fence changes; an existing unit test is edited; the real-disk default path changes behavior or is routed through the seam; a second filter copy or a second read path for the layout is added; either integration test still builds a `spools/` path or indexes `rig.fs.files` for a spool; a parameter other than `fs` is added; an existence assertion is weakened to one that passes on an empty listing; or a SQLite file is opened.

## Time budget
- expected: 20m
- stuck: 40m
- reason: One helper file with three small branches, about 8 appended unit tests and 5 mechanical call-site edits; the three test files run quickly, with no split needed
