---
state: draft
source: box:roadmap_row
priority: P3
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
- evidence-envelope
- spools-scratch-dir
- evidence-captures

## Context
- docs/roadmap.md#6. Owner decisions (decided 2026-11-13)
- docs/evidence-trail-plan.md#1. Record layout
- clutch/driver.py::Spool
- clutch/evidence/store.py::EvidenceStore.put_capture
- clutch/evidence/store.py::EvidenceStore.get_capture
- clutch/evidence/store.py::EvidenceStore.captures
- clutch/runner.py::harvest
- tests/evidence_records.py
- tests/unit/test_evidence_captures_store.py

## On-demand
- clutch/specs/ask/diagnose.md
- clutch/specs/ask/running.md
- docs/how-clutch-works.md

## Goal / Why
Roadmap row 63 (decision 12). After this ticket every per-attempt capture the engine writes (prompt, output, error, check, merge, regression and host-check output) lands in the evidence store as a capture, and no file is written under `<state_dir>/spools/`. `Spool.write(stem, attempt, name, text)` keeps its signature and calls `EvidenceStore.put_capture`; harvest reads its error, log and check output back through `captures` and `get_capture`; the two ask specs name `clutch evidence captures` instead of a `spools/` path; and the docs and the tests that assert `spools/` paths follow. There is one capture path for model calls and for attempt output, and the `spools/` row leaves the state-dir table. The graphics render directory and the retro window file already live under `<state_dir>/scratch/` (`spools-scratch-dir`) and are untouched.

Two existing capture rules cannot hold what `Spool` writes today, so this ticket changes them in `clutch/evidence/store.py`: attempt 0 is real (a ticket's first attempt, and `attempts/0/harvest.json` already exists), and a ticketless group is a surface name or eval name that may hold an underscore (`requisition_review`, `diagnose-eval-escalate_algorithm`). Capture `attempt` becomes an `int` (not a `bool`) of at least 0, and the capture group (the first argument, still named `stem` in the method signatures) must fully match `[a-z0-9][a-z0-9_-]{0,63}` instead of the ticket `STEM` rule. A spool stem of the form `<group>/<run_seq>` (retro and other run-sequenced ticketless calls) is stored under group `<group>` with the name prefixed by `<run_seq>/`; `Spool.write` does that split in one place.

## Boundary contract
### Attempt capture store
- disposition: replace
- owner: clutch/driver.py::Spool, writing through clutch/evidence/store.py::EvidenceStore
- consumers: `Driver.run_stage`, `clutch/requisition.py`, `clutch/stages.py` (check, merge, regression and host output), `clutch/retro.py`, `clutch/runner.py::harvest`, the `clutch evidence captures` verb, and the diagnose and running ask specs
- observable change: old contract: redacted text files at `<state_dir>/spools/<stem>/<attempt>/<name>`. Replacement: a capture with group `<stem>`, integer `attempt`, and the same `<name>`, redacted as a blob plus a pointer under `<state_dir>/evidence/captures/`. Run-sequenced spool stems `<group>/<run_seq>` become group `<group>` and name `<run_seq>/<name>`. `put_capture` and `get_capture` and `captures` accept attempt 0 and an underscore in the group. No file is written under `spools/`; nothing reads it; existing `spools/` files are stale and are neither read nor migrated. Failure of a write raises as `FileSystem.write` did; a name or group that fails the store rules raises `ValueError`, as before.
- compatibility: `Spool.write` keeps its argument list and its redaction; `harvest` artifacts (`harvest.json`) keep their fields, with `reason`, `stage_log_tail` and the training `check_outputs` computed from the same captures; the error pick changes from newest file mtime to last in `(attempt, name)` order, which is call order because names carry `call-NN`
- acceptance: a spool write followed by `get_capture` returns the redacted text; harvest output from captures equals harvest output from files in the existing harvest tests
- tests: tests/unit/test_evidence_captures_store.py, tests/unit/test_driver_spool_capture.py, tests/integration/test_harvest.py, tests/integration/test_driver.py, tests/integration/test_stages.py
- post-merge source of truth: clutch/driver.py::Spool and clutch/evidence/store.py

### Capture key rules
- disposition: extend
- owner: clutch/evidence/store.py (`EvidenceStore._validate_capture`, `EvidenceStore.captures`)
- consumers: `Spool`, harvest, and the `clutch evidence captures` verb, which passes arguments through unchanged
- observable change: attempt 0 is valid and listed (directory `0` is no longer skipped); group rule is `[a-z0-9][a-z0-9_-]{0,63}`; `"Bad Stem"`, `""` and `"../x"` are still refused; attempt `-1`, `True` and `"1"` are still refused; the verb's `--attempt 0` listing is now valid and `--attempt -1` is refused
- compatibility: captures written with attempt of 1 or more and valid groups read exactly as before; pointer schema, `CaptureNotFound`, `CaptureUnreadable` and `prune` are unchanged
- acceptance: unit tests flip the attempt-0 and underscore expectations and keep every other refusal
- tests: tests/unit/test_evidence_captures_store.py, tests/integration/test_evidence_captures_verb.py
- post-merge source of truth: clutch/evidence/store.py

## Scope in / Scope out
Scope in:
- `clutch/evidence/store.py`: the two rule changes above, and nothing else. The `stem` argument keeps its name; the `STEM` import becomes unused and is removed.
- `clutch/driver.py`: `Spool` takes the `EvidenceStore` and the `FileSystem` (keeping `_fs`, which `clutch/retro.py` uses), splits `<group>/<run_seq>` as described, and writes with `put_capture(group, attempt, name, text.encode())`; `Driver.from_config` builds it with `EvidenceStore(config.state_dir, fs, fs.read_bytes, fs.size, redactor.scrub)`. The `root` attribute and the `spools` path go.
- `clutch/runner.py::harvest`: replace the directory scan with `store.captures(stem, attempt)`: `reason` uses the last name ending `error.txt` in that order; `stage_log_tail` joins every capture whose last path segment is not `prompt.md`, in name order; the training `outputs` map uses captures whose name starts with `check/`, keyed by the name after `check/`, with `put_blob(get_capture(...))`. Build one store and reuse it for the existing `latest_stdout` and training calls.
- `clutch/specs/ask/diagnose.md` and `clutch/specs/ask/running.md`: replace each `spools/` path with `clutch evidence captures <stem>` (and `--attempt N --name NAME` to print one). Bump each file's `version` to the next minor above the version on main, never a literal target, and fence the test pin.
- Docs: `docs/how-clutch-works.md` (the call-spooling sentence near section 8, the redaction sentence naming spools, and the `spools/` row of the section 10.1 state-dir table, which is removed; the `evidence/` row already names captures), `clutch/docs/host-contract.md` (the two state-dir inventory lines naming attempt spools), `AGENTS.md` and `CLAUDE.md` (the one rule line naming attempt spools, to attempt captures, in both files in the same change). Update only those lines.
- Tests: every test that asserts a `spools/` path now asserts the capture instead. A new helper module `tests/capture_reads.py` with `capture_text(state_dir, stem, attempt, name, fs=None)` and `capture_names(state_dir, stem, attempt, fs=None)` reads through `EvidenceStore` (default `LocalFileSystem`; tests on an in-memory rig pass `rig.fs`), so no test hand-builds a pointer path. The listed test files change only their `spools/` assertions and any `Spool(...)` construction; `tests/integration/test_evidence_envelope.py` replaces its assertion that the `spools/` table row exists with one that no such row exists, and `tests/unit/test_evidence_envelope.py` drops the `spools` entries listing from its empty-state tuple. `tests/unit/test_evidence_captures_store.py` and `tests/integration/test_evidence_captures_verb.py` flip only the attempt-0 expectations and add the underscore group. New `tests/unit/test_driver_spool_capture.py` covers `Spool` (redaction, run-sequence split, attempt 0, no `spools/` entry) with `tmp_path` and the fake fs, and `tests/unit/test_runner_harvest_captures.py` covers harvest's three reads.
- `tests/integration/test_image_candidates_select.py`: the removal of `Spool.root` breaks its two `ctx.driver.spool.root / STEM / "0/render"` assertions (lines 96 and 180); replace each with an assertion that `capture_names(ctx.config.state_dir, STEM, 0)` holds no name starting with `render/`, using `tests/capture_reads.py`. Nothing else in that file changes.
- `tests/integration/test_kill_executor_abort.py`: `invoke()` builds `workspace=driver.spool.root.parent` (line 93) and every test in the file calls it, so the removal of `Spool.root` breaks them all; replace that expression with the directory the test's `build(tmp_path, ...)` already uses (for example `tmp_path` threaded into `invoke`, or the driver config's state_dir). Change nothing else in that file beyond its `spools/` assertions, if any.

Scope out: the graphics render directory and retro window file under `scratch/`; `CliAdapter` capture and the call records; the roadmap table (the driver rewrites it); any `spools/` cleanup of existing state directories; `clutch/redact.py` comment naming `Spool`; a new verb or help text.

Work is not split because every piece reads or writes the same capture path and the old and new path cannot coexist (no dual-path rule).

## Scope fence
- clutch/evidence/store.py
- clutch/driver.py
- clutch/runner.py
- clutch/specs/ask/diagnose.md
- clutch/specs/ask/running.md
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- AGENTS.md
- CLAUDE.md
- tests/capture_reads.py
- tests/harness/daemon_soak.py
- tests/unit/test_driver_spool_capture.py
- tests/unit/test_runner_harvest_captures.py
- tests/unit/test_specs.py
- tests/unit/test_evidence_captures_store.py
- tests/unit/test_evidence_envelope.py
- tests/unit/test_driver_panel_fanout.py
- tests/unit/test_key_scope.py
- tests/unit/test_host_check_selection.py
- tests/unit/test_check_timing.py
- tests/unit/test_requisition_dependents.py
- tests/unit/test_requisition_sibling_tickets.py
- tests/unit/test_requisition_stage_events.py
- tests/unit/test_route_kinds_filter.py
- tests/unit/test_runner_attempt_manifest.py
- tests/unit/test_stages_flake_coverage.py
- tests/unit/test_stages_host_lock.py
- tests/unit/test_stages_host_path.py
- tests/unit/test_projection_leftovers.py
- tests/unit/test_stages_render_check.py
- tests/integration/test_evidence_captures_verb.py
- tests/integration/test_evidence_envelope.py
- tests/integration/test_bug_gate.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_daemon_soak_runner.py
- tests/integration/test_diagnose.py
- tests/integration/test_driver.py
- tests/integration/test_echo_stage.py
- tests/integration/test_eval_harness.py
- tests/integration/test_harvest.py
- tests/integration/test_harvest_orphans.py
- tests/integration/test_host_contract.py
- tests/integration/test_host_mechanical.py
- tests/integration/test_image_candidates_select.py
- tests/integration/test_kill_executor_abort.py
- tests/integration/test_kill_failure_suppression.py
- tests/integration/test_kill_worker_stop.py
- tests/integration/test_merge.py
- tests/integration/test_mergequeue.py
- tests/integration/test_provider_cooldown_failover.py
- tests/integration/test_retro.py
- tests/integration/test_rework.py
- tests/integration/test_serve_admission.py
- tests/integration/test_stages.py
- tests/integration/test_triage.py
- tests/integration/test_watchdog.py
- tests/integration/test_watchdog_activation.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_driver_spool_capture.py` shows `Spool.write("work", 0, "check/verify-01.txt", text)` makes `capture_text(state_dir, "work", 0, "check/verify-01.txt")` return the redacted text, not the secret, and that `Spool.write("retro/3", 0, "retro/call-01/prompt.md", "x")` is stored as group `retro`, name `3/retro/call-01/prompt.md`, not under group `retro/3`.
2. The same file shows no file or directory named `spools` exists under `state_dir` after writes, `Spool.write("requisition_review", 0, ...)` succeeds, and a group `Bad Stem` raises `ValueError`, not a written file.
3. `./dev.py test tests/unit/test_evidence_captures_store.py` shows attempt 0 is accepted and listed first (`(0, name)` before `(1, name)`), attempt `-1`, `True` and `"1"` still raise `ValueError`, group `a_b` is accepted, and groups `"Bad Stem"`, `""` and `"../x"` still raise `ValueError`.
4. `./dev.py test tests/unit/test_runner_harvest_captures.py` shows harvest's `reason` is the text of the last `error.txt` capture in `(attempt, name)` order (not the first), `stage_log_tail` excludes `prompt.md` captures and includes the others, and the training `check_outputs` keys equal the capture names after `check/`, not names with the prefix.
5. `./dev.py test tests/integration/test_harvest.py tests/integration/test_harvest_orphans.py tests/integration/test_stages.py tests/integration/test_driver.py tests/integration/test_image_candidates_select.py tests/integration/test_kill_executor_abort.py` shows the existing harvest, stage, driver, image-candidate and kill-abort behaviours hold with captures, and `test_driver.py` shows a ticketless surface captures under its surface name.
6. `./dev.py test tests/integration/test_evidence_envelope.py tests/integration/test_evidence_captures_verb.py` shows the section 10.1 table has no `spools/` row, and `--attempt 0` on a listing exits 0, not 2, while `--attempt -1` exits 2.
7. `./dev.py test` passes with no file under `state_dir/spools` written by any test; `grep -rn '"spools"' clutch` prints no match in `clutch/`, read once in review.
8. `clutch/specs/ask/diagnose.md` and `clutch/specs/ask/running.md` name `clutch evidence captures` and contain no `spools/`, checked by `./dev.py test tests/unit/test_specs.py tests/integration/test_ask.py` and read once in review.

## Verification
```
./dev.py test
```

## Definition of rejected
- Any write to or read from `<state_dir>/spools/`, or a fallback that reads old spool files.
- A hand-built capture pointer path in a test or in engine code instead of the store methods.
- A change to the render directory, retro window file, call records, `CliAdapter`, or the roadmap table.
- Secrets reaching a blob unredacted, or `Spool.write` changing its argument list.
- A capture rule loosened beyond attempt 0 and the underscore group.

## Time budget
- expected: 30m
- stuck: 60m
- reason: not split because the writer, every reader and the path-asserting tests must change together; keeping both paths would break the no dual-path rule
