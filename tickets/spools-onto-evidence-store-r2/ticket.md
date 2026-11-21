---
state: draft
source: human
priority: P3
kind: chore
---

## Depends on
- evidence-captures
- spools-capture-keys
- spools-scratch-dir
- evidence-envelope

## Context
- clutch/evidence/store.py::capture_key
- clutch/evidence/store.py::EvidenceStore
- clutch/driver.py::Spool
- clutch/driver.py::Driver.from_config
- clutch/runner.py::harvest
- clutch/requisition.py
- clutch/retro.py
- tests/evidence_records.py
- tests/unit/test_runner_attempt_manifest.py
- tests/integration/test_driver.py
- docs/roadmap.md#6. Owner decisions (decided 2026-11-13)

## Goal / Why
Roadmap row 63 after its split (decision 12; rows 183 and 185 merged, row 186 documents). Today `Spool.write(stem, attempt, name, text)` writes a redacted file at `<state_dir>/spools/<stem>/<attempt>/<name>`, and `harvest` in `clutch/runner.py` reads that directory back. After this ticket every spool capture is an `EvidenceStore` capture and nothing writes or reads `<state_dir>/spools/`:

- `Spool.write` stores `redactor.scrub(text).encode()` with `EvidenceStore.put_capture(*capture_key(stem, attempt, name), data)`. This is the single production call of `capture_key`, so a write and a read cannot derive different keys. `Spool` takes the store and the redactor (`Spool(store, redactor)`); it keeps a private `_fs` equal to `store.fs` because `clutch/retro.py` and `Driver` already write through `driver.spool._fs` (scratch window file, retro report, storm producer), and those callers do not change. `Spool.root` is removed: nothing in `clutch/` reads it. `Driver.from_config` builds `EvidenceStore(config.state_dir, fs, fs.read_bytes, fs.size, redactor.scrub)` for it.
- `harvest` reads the captures of `(stem, attempt)` with `store.captures(stem, attempt)` and `store.get_capture`. Names that start with `run-<digits>/` are skipped (a rework or ticketless slot such as `ticket/3` folds under `(ticket, 0, "run-3/...")`, so they are not this attempt's logs). Of the rest: the error candidates are names whose last `/` segment is `error.txt`; the stage log is the names whose last segment is not `prompt.md`, in sorted name order, joined, then the last `HARVEST_TAIL_CHARS`; `check_outputs` is each name under `check/` keyed by the name without that prefix, valued `store.put_blob(captured bytes)`. The store keeps no modification time, so the "newest error" the old code chose by file mtime is now the greatest name in sorted order (call numbers are zero padded, so the later call of a stage wins). Previously `rglob` also walked slot sub-directories such as `ticket/3/0/...` into attempt 3's tail; that accident ends with the filter above.
- Each of the three stored-value kinds below is defined here, none is new on disk: a capture pointer and blob are the existing `put_capture` format; the harvest `reason` and `stage_log_tail` are the existing `Harvest` fields built from capture text decoded as UTF-8 with `errors="replace"`.

Every stored field is validated by the store's rules (stem `[a-z0-9][a-z0-9_-]{1,127}`, attempt an `int` at least 0, name `[A-Za-z0-9][A-Za-z0-9._/-]{0,199}`) through `capture_key`; `Spool.write` adds no rule of its own.

Named outcomes. `Spool.write` `stored`: the capture exists and `get_capture` returns the scrubbed bytes. `Spool.write` `refused`: `capture_key` raises `ValueError`, the exception propagates (a bad stem is a programming error, never swallowed) and nothing is written. `harvest` `read`: as above. `harvest` `skipped-unreadable`: a capture that raises `CaptureNotFound` or `CaptureUnreadable` is skipped and the rest are used, because the harvest is the failure record and one bad pointer must not erase it. `harvest` `empty`: no captures for `(stem, attempt)` gives `reason = terminal` when there are no findings, an empty tail and `{}` check outputs, as an absent directory did.

Every test that asserts a `spools/` path flips in this change (no dual path). Tests read captures through one new helper module, `tests/spool_captures.py`, so each flipped assertion is a one-line call and none re-derives the key rule.

## Boundary contract
### Spool capture writer
- disposition: replace
- owner: clutch/driver.py (`Spool`, `Driver.from_config`)
- consumers: `Driver.run` and `Driver.run_panel` (prompt, output, error captures), `clutch/requisition.py`, `run_host_command` and the regression writer in `clutch/stages.py` (host, verify and regression logs); `clutch/retro.py` and the storm producer use `driver.spool._fs` only
- observable change: captures land at `<state_dir>/evidence/captures/<stem>/<attempt>/<quoted name>.json` plus a blob, not at `<state_dir>/spools/...`; `Spool(root, redactor, fs)` becomes `Spool(store, redactor)`; `Spool.root` is gone; a spool slot that `capture_key` refuses raises `ValueError`
- compatibility: old files already under `<state_dir>/spools/` are never read or deleted (they are disposable per-attempt scratch of earlier runs); no stored evidence changes shape
- acceptance: criteria 1, 2 and 6
- tests: tests/unit/test_spool_store_switch.py; the flipped integration tests
- post-merge source of truth: clutch/driver.py

### Harvest capture reader
- disposition: replace
- owner: clutch/runner.py (`harvest`)
- consumers: the run-terminal harvest, `harvest_orphan`, the attempt manifest's `check_outputs`
- observable change: harvest reads from the store; the `run-<n>/` filter, the sorted-name "newest error" rule and the `skipped-unreadable` outcome as the Goal states
- compatibility: `Harvest` fields and `check_outputs` keys are unchanged for a plain attempt; a slot's `run-<n>/` captures no longer appear in another attempt's tail
- acceptance: criteria 3, 4 and 5
- tests: tests/unit/test_spool_store_switch.py, tests/unit/test_runner_attempt_manifest.py, tests/integration/test_harvest_orphans.py, tests/integration/test_harvest.py
- post-merge source of truth: clutch/runner.py

### Capture read helper for tests
- disposition: create
- owner: tests/spool_captures.py
- consumers: about 28 existing test modules and the soak harness that read a spool file today (listed in the fence)
- observable change: new functions `capture_store(state_dir, fs=None)`, `capture_text(state_dir, stem, attempt, name, fs=None)` and `capture_names(state_dir, stem, attempt, fs=None)`; no production code imports it
- closest existing: `tests/evidence_records.py` builds a store for records only and cannot read a capture by spool slot; `EvidenceStore.get_capture` needs a key already folded by `capture_key`
- earning reason: more than 25 test modules need the same fold-and-read with the same default filesystem, and the fake-filesystem rigs (`rig.fs`) need the store's filesystem passed in; one helper keeps the fold in `capture_key`
- compatibility: new module; the test-only helper `spool()` in tests/integration/test_driver.py is replaced by it
- acceptance: criterion 7
- tests: the flipped tests that call it
- post-merge source of truth: tests/spool_captures.py

## Scope in / Scope out
Scope in:
- `clutch/driver.py`: `Spool` as the Goal states (constructor, `write`, `_fs`, no `root`), `Driver.from_config` builds the store, and the import of `EvidenceStore` and `capture_key`. Nothing else in the file changes.
- `clutch/runner.py`: the spool-reading lines at the top of `harvest` and the `check` outputs line in its training branch, as the Goal states. Nothing else changes.
- New `tests/spool_captures.py` with the three helpers, a `clutch:meta` header with a non-empty one-line `purpose` (for example `# purpose: Read spool captures from the evidence store in tests.`) and `# kind: test`.
- New `tests/unit/test_spool_store_switch.py` with a `clutch:meta` header and a non-empty `purpose`: the writer, harvest and no-`spools/` cases of criteria 1 to 6.
- Flip every existing assertion that names a `spools/` path or `Spool.root` to the helper, keeping what it asserts (presence, content, absence). In `tests/integration/test_harvest_orphans.py` the setup that created a spool file now calls `put_capture(*capture_key(...))`. In `tests/unit/test_runner_attempt_manifest.py` the `check/output.txt` setup does the same. Unit tests that construct `Spool(tmp_path / "spool", redactor, fs)` pass a store instead: `test_driver_panel_fanout.py`, `test_key_scope.py`, `test_route_kinds_filter.py`; the fake-path assertion in `test_driver_panel_fanout.py` becomes a `capture_names` check. The dead `spools/work/4/render` assertion in `tests/unit/test_stages_render_check.py` is deleted (the render directory moved to scratch in `spools-scratch-dir`). `tests/integration/test_driver.py` drops its `spool()` helper and `tests/integration/test_kill_executor_abort.py` stops importing it. `tests/harness/daemon_soak.py` and `tests/integration/test_daemon_soak_runner.py` read the three soak spool logs through the helper (`test_daemon_soak_runner.py` also builds a `.clutch/state/spools/...` path string as the expected fault-summary source: it becomes the capture's description the harness now emits, so edit both together).
- A negative assertion (`not ... .exists()`, `not list(...rglob(...))`) flips to `capture_names` not containing the name, never deleted, so it keeps ruling something out. `tests/integration/test_watchdog.py` and `tests/integration/test_retro.py` are such cases.
- The hot files `tests/integration/test_stages.py`, `tests/integration/test_mergequeue.py` and `tests/integration/test_daemon_composition.py` are fenced because each asserts a `spools/` path (test_stages: three, test_mergequeue: six, test_daemon_composition: one); only those assertions change there.

Scope out:
- `clutch/retro.py`, `clutch/requisition.py`, `clutch/stages.py`, `clutch/redact.py`: they call `driver.spool.write` or `driver.spool._fs` and keep working; the `redact.py` docstring line naming `Spool` is row 186.
- The two ask prompt specs that name a `spools/` path, the architecture document, the host contract guide, and the `spools/` lines of the two conduct files: `spools-evidence-docs` (row 186) rewrites them. Until it merges they still name `spools/`; that is the accepted window. `tests/integration/test_evidence_envelope.py` pins the `spools/` row of the architecture document and stays untouched for the same reason.
- `tests/unit/test_evidence_envelope.py`, `test_images_gate.py`, `test_stages_candidates_select.py` and the unit fakes `spool=SimpleNamespace(write=...)`: they pass a fake, read no `spools/` file and are not edited.
- Store rules, `capture_key` and `clutch evidence captures`: unchanged (`spools-capture-keys`, merged).
- Overlap: `index-build-verb-r1` is the only in-flight ticket; it shares no fenced file with this one, so merge order does not matter.

## Scope fence
- clutch/driver.py
- clutch/runner.py
- tests/spool_captures.py
- tests/unit/test_spool_store_switch.py
- tests/unit/test_driver_panel_fanout.py
- tests/unit/test_key_scope.py
- tests/unit/test_route_kinds_filter.py
- tests/unit/test_runner_attempt_manifest.py
- tests/unit/test_stages_render_check.py
- tests/integration/test_echo_stage.py
- tests/integration/test_watchdog_activation.py
- tests/integration/test_harvest_orphans.py
- tests/integration/test_serve_admission.py
- tests/integration/test_eval_harness.py
- tests/integration/test_merge.py
- tests/integration/test_stages.py
- tests/integration/test_retro.py
- tests/integration/test_kill_failure_suppression.py
- tests/integration/test_kill_executor_abort.py
- tests/integration/test_kill_worker_stop.py
- tests/integration/test_rework.py
- tests/integration/test_bug_gate.py
- tests/integration/test_mergequeue.py
- tests/integration/test_driver.py
- tests/integration/test_watchdog.py
- tests/integration/test_provider_cooldown_failover.py
- tests/integration/test_host_mechanical.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_image_candidates_select.py
- tests/integration/test_triage.py
- tests/integration/test_daemon_soak_runner.py
- tests/harness/daemon_soak.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_spool_store_switch.py` shows `Spool.write("work/1", 2, "review/call-01/output.txt", text)` makes `store.get_capture("work", 2, "run-1/review/call-01/output.txt")` return the scrubbed bytes, with a configured secret replaced by its redaction marker and no file created under `<state_dir>/spools`; `Spool.write("my-ticket", 0, "merge/host-01.txt", ...)` is readable at `("my-ticket", 0, "merge/host-01.txt")`; a second write to one key replaces the first, not appends.
2. The same file shows `Spool.write("Bad Stem", 1, "x", "t")` and `Spool.write("work/01", 1, "x", "t")` raise `ValueError` (the `refused` outcome) and `store.captures("work")` stays empty, not a file under a sanitized name.
3. The same file shows `harvest` for `(stem, attempt)` with captures `implement/call-01/error.txt`, `implement/call-02/error.txt`, `implement/call-01/prompt.md`, `check/verify-01.txt` and `run-3/rework/call-01/error.txt` gives `reason` equal to the `implement/call-02/error.txt` text (the sorted-last error, not the first, not the `run-3/` one), a `stage_log_tail` that contains the verify log and neither prompt text nor the `run-3/` text, and `check_outputs` equal to `{"verify-01.txt": <blob ref>}`, not keyed `check/verify-01.txt`.
4. The same file shows a capture whose pointer is corrupted (`CaptureUnreadable`) is skipped and the other captures still feed `reason` and `stage_log_tail` (`skipped-unreadable`), and a `(stem, attempt)` with no captures gives `reason == terminal`, an empty tail and `check_outputs == {}` (`empty`), not an exception.
5. `./dev.py test tests/unit/test_runner_attempt_manifest.py tests/integration/test_harvest_orphans.py tests/integration/test_harvest.py` passes with the check output and the orphan spool error set up through `put_capture`, showing the manifest's `check_outputs["output.txt"]` blob is `b"check failure"` and the orphan harvest reason contains `provider died with useful detail`.
6. `rg -n '"spools"|spools/' clutch --glob '*.py'` finds no write or read of a `spools` path (a docstring may remain: row 186), and `tests/unit/test_spool_store_switch.py` runs a real `Driver` call and a merge-slot host log through a temporary state dir and shows `<state_dir>/spools` does not exist afterwards, not an empty directory.
7. `capture_key` has one production call site: `rg -n 'capture_key\(' clutch` lists the definition in `clutch/evidence/store.py` and exactly one call in `clutch/driver.py`, not a second in `clutch/runner.py`; `harvest` obtains names from `store.captures` and never builds a key. `tests/spool_captures.py` helpers fold through `capture_key` and the test shows `capture_text(state, "work/1", 2, name)` equals the `Spool.write` content.
8. `./dev.py test tests/unit tests/integration` passes with every flipped assertion reading through `tests/spool_captures.py`: `rg -n 'spools/|"spools"' tests` finds only the `spools-evidence-docs`-owned `tests/integration/test_evidence_envelope.py` and `tests/unit/test_evidence_envelope.py` hits (the unchanged document-row pin and the empty-directory check) and the new test's `<state_dir>/spools` absence check, never a path read or written as a spool file.

## Verification
```
./dev.py test tests/unit tests/integration
uv run ruff format --check .
```

## Definition of rejected
`Spool` still writes `<state_dir>/spools/`, or writes both places; harvest reads a `spools/` path or keeps a fallback to it; a second function or inline split derives a capture key; a refused key is swallowed or sanitized into a different name; harvest includes `run-<n>/` captures in another attempt's tail; a flipped test is deleted or weakened to one that also passes on the old behavior; a store rule, `capture_key`, `clutch/retro.py`, a prompt spec, a document or a conduct file changes; a new test or helper is added to a hot test file; or a file outside the fence changes.

## Time budget
- expected: 30m
- stuck: 60m
- reason: the source change is two small edits; the time is the mechanical flip of about 70 `spools/` assertions across 28 test files, which a dual path would only make longer, so it cannot be split by test file without leaving main with two live spool locations.
