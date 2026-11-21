# Supervisor Rework escalated

- trigger: premise_failed
- outcome: gate_failed
- action: update

## Findings

- `supervise_edit`: the proposal changes `## Goal / Why` -- escalate to the operator: the stem stays in the Reject queue; edit tickets/spools-onto-evidence-store-r2/ticket.md, then `clutch ticket confirm spools-onto-evidence-store-r2`, or retire it with `clutch ticket reject spools-onto-evidence-store-r2`

## Proposed ticket

````markdown
---
state: confirmed
source: human
priority: P3
kind: chore
---

## Depends on
- evidence-captures
- spools-capture-keys
- spools-tests-via-helper
- spools-tests-via-helper-driver
- spools-tests-via-helper-fake-fs

## Context
- clutch/evidence/store.py::capture_key
- clutch/evidence/store.py::EvidenceStore
- clutch/driver.py::Spool
- clutch/driver.py::Driver.from_config
- clutch/runner.py::harvest
- tests/spool_captures.py
- tests/unit/test_spool_captures.py
- tests/unit/test_runner_attempt_manifest.py
- tests/unit/test_key_scope.py
- tests/integration/test_kill_executor_abort.py
- tests/integration/test_requisition.py
- tests/integration/test_driver.py
- tests/integration/test_spec_sibling_tickets.py

## Goal / Why
Roadmap row 63 (`spools-onto-evidence-store-r2`), flip only. Every test that asserted a `spools/` path already reads captures through `tests/spool_captures.py` (`read_capture`, `write_capture`, `list_captures`, each with an optional `fs` keyword), so this change moves production and that one helper together. After it, every spool capture is an `EvidenceStore` capture and nothing creates, writes or reads `<state_dir>/spools/`.

Today `Spool.write(stem, attempt, name, text)` writes a redacted file at `<state_dir>/spools/<stem>/<attempt>/<name>` and `harvest` in `clutch/runner.py` reads that tree back. Verified by reading the merged code: `Spool(root, redactor, fs)` is built only in `Driver.from_config` (`Spool(config.state_dir / "spools", redactor, fs or LocalFileSystem())`) and in tests; `Spool.root` is read only by `tests/integration/test_kill_executor_abort.py`; `Spool._fs` is read by `clutch/retro.py` (two writes) and `Driver` (storm producer); `Spool._redactor` is read by `tests/unit/test_projection_leftovers.py`; `clutch/requisition.py` and `clutch/stages.py` only call `spool.write`.

Spool. The constructor stays `Spool(state_dir, redactor, fs)`; its first argument now means the state directory, not the `spools` directory. It builds one store, `EvidenceStore(state_dir, fs, fs.read_bytes, fs.size, redactor.scrub)`, as `self._store`, and keeps `self._redactor` and `self._fs` (`_fs is fs`, so `retro.py` and the storm producer are untouched). `write` calls `self._store.put_capture(*capture_key(stem, attempt, name), self._redactor.scrub(text).encode())`; `put_blob` scrubs the text a second time, which is harmless. `Spool.root` is deleted. `Driver.from_config` passes `config.state_dir`. This is the one production call of `capture_key`. The simpler alternative rejected: `Spool(store, redactor)`, which makes every one of the seven test constructors build a store by hand; keeping the three-argument shape changes one argument per call site and the first captures assertion (criterion 1) fails loudly if a call site still passes a `spools` directory.

Harvest. `harvest` builds one `EvidenceStore(ctx.config.state_dir, ctx.fs, ctx.fs.read_bytes, ctx.fs.size, ctx.driver.redactor.scrub)` at the top and reuses it for the events tail and the training branch (today it builds two). It lists `store.captures(stem, attempt)` and drops every name that starts with `run-<digits>/`. A rework or ticketless slot such as spool stem `ticket/3` folds under `("ticket", 0, "run-3/...")` in `capture_key`, so those names are not this attempt's logs. Worked example: for `harvest(stem="ticket", attempt=0)` with captures `implement/call-01/error.txt`, `check/verify-01.txt` and `run-3/review/call-01/error.txt`, the kept names are the first two. Of the kept names, in sorted name order: the error candidates are names whose last `/` segment is `error.txt`; the stage log is every name whose last segment is not `prompt.md`, each capture decoded as UTF-8 with `errors="replace"`, joined, then the last `HARVEST_TAIL_CHARS`; `check_outputs` is each name starting with `check/`, keyed by the name without that prefix, valued `store.put_blob(captured bytes)`. The old rule picked the newest error by file modification time; the store keeps none, so the replacement is exactly the error name that is greatest in sorted order (call numbers are zero padded, so the later call of a stage wins). The old `rglob` also walked slot sub-directories such as `spools/ticket/3/0/...` into attempt 3's tail; that accident ends with the `run-<n>/` filter.

Named outcomes. `Spool.write` `stored`: the capture exists and `get_capture` returns the scrubbed bytes; a second write to one key replaces the first. `Spool.write` `refused`: `capture_key` raises `ValueError`, it propagates, nothing is written. `harvest` `read`: as above. `harvest` `skipped-unreadable`: a capture whose read raises `CaptureNotFound`, `CaptureUnreadable` or `OSError` is skipped and the rest are used (the store lets an `OSError` from a pointer read escape; the harvest is the failure record, one bad pointer must not erase it). `harvest` `empty`: no kept captures gives `reason = terminal` when there are no findings, an empty tail and `{}` check outputs, as an absent directory did. Every stored field is validated by `capture_key` (stem rule, attempt `int` at least 0, name rule, `run-<n>/` folding); `Spool.write` adds no rule of its own.

Helper. `tests/spool_captures.py` flips to the store with every signature and the `fs` keyword unchanged. Each function first calls `capture_key` (so the same `ValueError`s fire before any filesystem access, and an absent state directory stays absent), then builds `EvidenceStore(state_dir, fs or LocalFileSystem(), ...)` per call (so a test that monkeypatches `fs.read_bytes` is seen). `read_capture` returns `get_capture` bytes of the folded key, mapping `OSError` to `CaptureUnreadable` as it does today. `write_capture` keeps its bytes-only `ValueError` and calls `put_capture`. `list_captures(state_dir, spool_stem, attempt=None)` returns the sorted `(attempt, name)` pairs of `store.captures(folded stem[, attempt])`: for a stem without a slash it drops names starting with `run-<digits>/`; for `work/1` it keeps only names starting with `run-1/` and strips that prefix, so each spool slot lists as it does today. The oracle for "identical results before and after" is `tests/unit/test_spool_captures.py`, which passes with only the edits listed in Scope in; every other assertion in it is unchanged.

Two existing tests rest on the old layout and change minimally (found by the previous run). `tests/integration/test_requisition.py` passes `stem_slot="s"` in its `run` helper (line 113) and in a second call (line 203); `capture_key` rejects the one-character stem (`_STEM` needs at least two characters), so every requisition test that writes a spool fails. Both become `stem_slot="req-slot"` and the two journal-key expectations that pin it (lines 187 and 228, `llm/s/0/...`) become `llm/req-slot/0/...`. `tests/integration/test_spec_sibling_tickets.py::test_sibling_instruction_and_real_render` imports that same `run` helper, which is why it failed on the candidate and passed on base; the fixture fix repairs it and it is not edited. `tests/integration/test_driver.py::test_configured_secret_value_never_reaches_spool_or_engine_log` asserts at line 376 that files named `prompt.md`, `output.txt` and `error.txt` exist under the state directory; the store names its files by quoted key plus `.json` and blobs, so that one assertion changes to the store layout through the helper.

Retro, requisition and stages are unchanged and verified above. Docs and the two ask specs that name `spools/` are row 186 (`spools-evidence-docs`); until it merges they still name `spools/`, the accepted window.

## Boundary contract
### Spool capture writer
- disposition: replace
- owner: clutch/driver.py (`Spool`, `Driver.from_config`)
- consumers: `Driver.run` and `Driver.run_panel`, `clutch/requisition.py`, `run_host_command` and the regression writer in `clutch/stages.py` (all call `spool.write`); `clutch/retro.py` and the storm producer read `spool._fs`; `tests/unit/test_projection_leftovers.py` reads `spool._redactor`
- observable change: captures land at `<state_dir>/evidence/captures/<stem>/<attempt>/<quoted name>.json` plus a blob, never under `<state_dir>/spools/`; the first constructor argument becomes the state directory; `Spool.root` is gone; a slot `capture_key` refuses raises `ValueError`
- compatibility: files already under `<state_dir>/spools/` are never read or deleted (disposable scratch of earlier runs); no stored evidence changes shape
- acceptance: criteria 1, 2, 6, 7, 8 and 9
- tests: tests/unit/test_spool_store_switch.py, tests/integration/test_spool_store_source.py, tests/integration/test_requisition.py, tests/integration/test_driver.py, the existing integration suite reading through the helper
- post-merge source of truth: clutch/driver.py

### Harvest capture reader
- disposition: replace
- owner: clutch/runner.py (`harvest`)
- consumers: the run-terminal harvest, `harvest_orphan`, the attempt manifest's `check_outputs`
- observable change: harvest reads the store; `run-<n>/` names are excluded; the newest error is the greatest name in sorted order; an unreadable capture is skipped
- compatibility: `Harvest` fields and `check_outputs` keys are unchanged for a plain attempt; a slot's captures no longer reach another attempt's tail
- acceptance: criteria 3, 4 and 5
- tests: tests/unit/test_spool_store_switch.py, tests/unit/test_runner_attempt_manifest.py, tests/integration/test_harvest_orphans.py, tests/integration/test_harvest.py
- post-merge source of truth: clutch/runner.py

### Spool capture test helper
- disposition: replace
- owner: tests/spool_captures.py
- consumers: the 26 test modules that import it
- observable change: body reads and writes the store instead of `<state_dir>/spools/`; signatures, `fs` keyword, return values and raised exceptions are unchanged
- compatibility: preserves every helper result the callers rely on; only the on-disk layout the helper's own test pins changes
- acceptance: criterion 6
- tests: tests/unit/test_spool_captures.py
- post-merge source of truth: tests/spool_captures.py

## Scope in / Scope out
Scope in:
- `clutch/driver.py`: `Spool` as the Goal states, `Driver.from_config` passing `config.state_dir`, and the `EvidenceStore` and `capture_key` imports. Nothing else changes.
- `clutch/runner.py`: the spool-reading lines of `harvest` (the first lines through `stage_log_tail`) and the `check` outputs lines of its training branch, plus reusing one store. Nothing else changes.
- `tests/spool_captures.py`: the body flip as the Goal states. It carries a `clutch:meta` hash header: after the edit run `uv run clutch meta refresh tests/spool_captures.py`.
- `tests/unit/test_spool_captures.py` (also has a hash header; run `uv run clutch meta refresh` on it after editing). Only the assertions that pin the old layout change: (a) the `spool` fixture and the `writers` line pass `tmp_path`, not `tmp_path / "spools"`; (b) `test_read_errors` reads `"dir"` where only `"dir/file"` exists and now expects `CaptureNotFound` (the store has no directories), and `CaptureUnreadable` is asserted on a corrupted pointer file written under `tmp_path / "evidence/captures/work/1/"`; (c) in `test_listing` and `test_fake_listing_matches_disk` the two `spool.write` calls of `run-1/invalid` and `bad name` become `pytest.raises(ValueError)` checks (the writer now refuses them, so they can no longer seed junk), and the `spools/item/nope`, `spools/item/0/empty` and non-ASCII attempt directory seeds are deleted (the store's own listing of junk entries is pinned by `tests/unit/test_evidence_captures_store.py`); (d) in `test_fake_round_trip_and_overwrite` the two `fake_fs.files[path]` assertions and the `path` variable go, the `read_capture` assertions stay; (e) in `test_fake_read_errors` the `fake_fs.mkdir(tmp_path / "spools/work/0/dir")` line goes and the `"dir"` read stays `CaptureNotFound`.
- `tests/integration/test_requisition.py` (has a `clutch:meta` header; refresh after editing): only the two `stem_slot="s"` arguments (lines 113 and 203) become `stem_slot="req-slot"` and the two journal-key expectations at lines 187 and 228 change `llm/s/0/` to `llm/req-slot/0/`. Nothing else changes.
- `tests/integration/test_driver.py` (has a `clutch:meta` header; refresh after editing): in `test_configured_secret_value_never_reaches_spool_or_engine_log` only the line-376 assertion changes, to `assert "engine.log" in {p.name for p in files}` plus `assert {n.rsplit("/", 1)[-1] for _, n in list_captures(state, "t-echo")} >= {"prompt.md", "output.txt", "error.txt"}`, with `list_captures` added to the existing `tests.spool_captures` import. The `SECRET not in p.read_text()` loop over every state file and the two `read_capture` redaction assertions stay unedited.
- Constructor call sites, one line each: `tests/unit/test_driver_panel_fanout.py` (`rig`), `tests/unit/test_key_scope.py`, `tests/unit/test_route_kinds_filter.py` and `tests/unit/test_review_panel_use.py` (two sites) pass `tmp_path` or `state_dir` instead of a `spools` directory. `tests/integration/test_kill_executor_abort.py` `invoke` passes `workspace=driver.spool._store.root.parent` (the state directory, what `driver.spool.root.parent` was) because `Spool.root` is gone. Any of these files that begins with a `# clutch:meta` header is refreshed with `uv run clutch meta refresh <path>` after the edit.
- New `tests/unit/test_spool_store_switch.py` (criteria 1 to 4 and 6, the `Spool` and `harvest` cases through `tmp_path` and a `SimpleNamespace` context like the one in `tests/unit/test_runner_attempt_manifest.py`, built inline, not imported) and new `tests/integration/test_spool_store_source.py` (criteria 7 and 8, source reads anchored on `Path(__file__)`). The implementer creates each header with `uv run clutch meta refresh <file>` and edits only the `# purpose:` line to a non-empty one-line sentence.

Scope out:
- `clutch/retro.py`, `clutch/requisition.py`, `clutch/stages.py`, `clutch/redact.py`: they call `spool.write` or `spool._fs` and keep working.
- `tests/integration/test_spec_sibling_tickets.py`: it imports `run` from `tests/integration/test_requisition.py` and passes once that fixture's stem is valid; it is not edited.
- Every document, the two ask specs and the two conduct files: `spools-evidence-docs` (row 186).
- Tests that pass a fake `spool=SimpleNamespace(write=...)`, and tests asserting `<state_dir>/spools` is absent or empty (`tests/integration/test_watchdog.py`, `tests/unit/test_evidence_envelope.py`): they pass unchanged and are not edited; `tests/integration/test_evidence_envelope.py` pins a document row and stays untouched.
- Store rules, `capture_key`, `clutch evidence captures`: unchanged.
- Overlap: `index-consumers-implement-hint` (running) fences `clutch/stages.py`, `clutch/context.py`, `clutch/config.py`, the implement spec and its pins, none of which are fenced here.

## Scope fence
- clutch/driver.py
- clutch/runner.py
- tests/spool_captures.py
- tests/unit/test_spool_captures.py
- tests/unit/test_driver_panel_fanout.py
- tests/unit/test_key_scope.py
- tests/unit/test_route_kinds_filter.py
- tests/unit/test_review_panel_use.py
- tests/integration/test_kill_executor_abort.py
- tests/integration/test_requisition.py
- tests/integration/test_driver.py
- tests/unit/test_spool_store_switch.py
- tests/integration/test_spool_store_source.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_spool_store_switch.py` shows `Spool(tmp_path, Redactor({"KEY": "s3cret"}), LocalFileSystem()).write("work/1", 2, "review/call-01/output.txt", "a s3cret b")` makes `EvidenceStore.get_capture("work", 2, "run-1/review/call-01/output.txt")` return the scrubbed bytes without `s3cret`; `write("my-ticket", 0, "merge/host-01.txt", "x")` is readable at `("my-ticket", 0, "merge/host-01.txt")`; a second write to one key leaves only the second text, not both; and `tmp_path / "spools"` does not exist afterwards (not an empty directory).
2. The same file shows `Spool.write("Bad Stem", 1, "x", "t")` and `Spool.write("work/01", 1, "x", "t")` raise `ValueError` (outcome `refused`) and `store.captures("work")` stays `[]`, no file under a sanitized name.
3. The same file shows `harvest` for `("ticket", 0)` with captures `implement/call-02/error.txt` written first, then `implement/call-01/error.txt`, `implement/call-01/prompt.md` (text `SECRET PROMPT`), `check/verify-01.txt` and `run-3/review/call-01/error.txt` (text `SLOT LOG`) gives `reason` equal to the `implement/call-02/error.txt` text (the greatest sorted name, not the newest written, which is what the old modification-time rule would pick, and not the `run-3/` one), a `stage_log_tail` containing the verify log and neither `SECRET PROMPT` nor `SLOT LOG`, and `check_outputs` equal to `{"verify-01.txt": <blob ref>}`, not keyed `check/verify-01.txt`.
4. The same file shows `skipped-unreadable`: a pointer corrupted to invalid JSON (`CaptureUnreadable`) and a pointer read raising `PermissionError` (`OSError`) are each skipped while the other captures still feed `reason` and `stage_log_tail`; and `empty`: a `(stem, attempt)` with no captures gives `reason == terminal`, `stage_log_tail == ""` and `check_outputs == {}` with the training branch on, not an exception.
5. `./dev.py test tests/unit/test_runner_attempt_manifest.py tests/integration/test_harvest_orphans.py tests/integration/test_harvest.py` passes unedited, showing the manifest's `check_outputs["output.txt"]` blob is `b"check failure"` and the orphan harvest reason contains `provider died with useful detail`, both seeded through `write_capture` and read back by the new harvest.
6. `./dev.py test tests/unit/test_spool_captures.py` passes with only the edits (a) to (e) in Scope in, every other assertion unedited, so each of `read_capture`, `write_capture` and `list_captures` gives the results it gave before on disk and on `FakeFileSystem` (round trip, overwrite, `CaptureNotFound`, `CaptureUnreadable`, `ValueError` before any filesystem access with an absent state directory staying absent, sorted and attempt-filtered listing with `work` and `work/1` kept apart, fake listing equal to disk listing); and `./dev.py test tests/integration/test_driver.py tests/unit/test_projection_leftovers.py` passes, with `tests/unit/test_projection_leftovers.py` unedited and `tests/integration/test_driver.py` edited only at the line-376 assertion as Scope in states, showing `Driver.from_config` wires the store at `<state_dir>/evidence`, no state file contains the configured secret, and `driver.spool._redactor` is still the driver's redactor.
7. `./dev.py test tests/integration/test_spool_store_source.py` shows no `.py` file under `clutch/` contains the string literal `"spools"` as a path component, not merely that `driver.py` and `runner.py` do not.
8. The same file shows `capture_key(` is called exactly once under `clutch/` outside its definition in `clutch/evidence/store.py` (in `clutch/driver.py`), and `clutch/runner.py` never builds a key, not a second call in `harvest`.
9. `./dev.py test tests/integration/test_requisition.py tests/integration/test_spec_sibling_tickets.py` passes, with `tests/integration/test_requisition.py` edited only at the four `s` stem lines named in Scope in and `tests/integration/test_spec_sibling_tickets.py` unedited.

## Verification
```
./dev.py test tests/unit tests/integration
uv run ruff format --check .
```

## Definition of rejected
`Spool` still writes `<state_dir>/spools/` or writes both places; harvest reads a `spools/` path or falls back to it; a second function or inline split derives a capture key; a refused key is swallowed or sanitized; harvest includes `run-<n>/` captures in another attempt's tail; the "newest error" is chosen by write order; a helper signature, `fs` keyword or exception changes beyond the edits listed; a test other than those listed is edited, or a listed test is edited beyond its listed lines; a flipped assertion is deleted without the listed reason or weakened to pass on the old behavior; the secret-absence loop in `tests/integration/test_driver.py` is removed or narrowed; a store rule, `capture_key`, `clutch/retro.py`, a spec, a document or a conduct file changes; or a file outside the fence changes.

## Time budget
- expected: 30m
- stuck: 60m
- reason: two small production edits and one helper body, but the ticket also rewrites about five assertion groups in the helper's own test, touches seven constructor sites, fixes two fixture-level test lines and adds two new test files; the full-suite run is the longest step, and the helper flip cannot be split from production without leaving main with two live spool locations.
````
