---
state: draft
source: human
priority: P3
kind: chore
---

## Depends on
- spools-test-helper

## Context
- docs/roadmap.md#6. Owner decisions (decided 2026-11-13)
- tests/spool_captures.py
- tests/unit/test_spool_captures.py
- tickets/spools-test-helper/ticket.md
- clutch/evidence/store.py::capture_key
- tests/integration/test_mergequeue.py::test_verification_uses_rebased_worktree
- tests/integration/test_daemon_soak_runner.py::test_daemon_soak_requires_member_local_evidence

## Goal / Why
Roadmap row 190, the integration half of row 63's test split, part 1 of 3 (the merge-admission and soak family; the remaining parts are the roadmap rows `spools-tests-via-helper-driver` and `spools-tests-via-helper-fake-fs`, each filed as a roadmap row by the owner, not by this ticket). Row 63 (`spools-onto-evidence-store-r2`) makes `Spool` write through `put_capture` and stop writing `<state_dir>/spools/`; the helper body in `tests/spool_captures.py` flips there. Every integration test that asserts or reads a spool file by a `spools/` path would break at the flip, so first they reach spool files through `read_capture` and `list_captures` from `tests/spool_captures.py` (merged by `spools-test-helper`). No production file changes; the helper body still reads `spools/` exactly as `Spool.write` writes it, so there is one writer and no dual path.

A grep over `tests/integration`, `tests/harness` and `tests/*.py` for `spools`, `Spool(`, `.spool` and `spool.root` finds 21 integration modules that assert or read a spool path or the spool root. They split by family so each part fits one run (about 50 call sites in all; part 1 has about 27 sites in 8 files):

- Part 1, this ticket: `test_mergequeue`, `test_merge`, `test_stages`, `test_host_mechanical`, `test_bug_gate`, `test_daemon_composition`, `test_daemon_soak_runner`, `test_serve_admission` (all merge, check and admission captures, on a real filesystem).
- Part 2, `spools-tests-via-helper-driver`: `test_driver`, `test_echo_stage`, `test_kill_worker_stop`, `test_kill_failure_suppression`, `test_harvest_orphans`, `test_rework`, `test_triage`, `test_eval_harness`, `test_watchdog`, `test_retro`, `test_image_candidates_select` (driver, kill and retro captures, including the `driver.spool.root` and `driver.spool._fs` sites).
- Part 3, `spools-tests-via-helper-fake-fs`: `test_watchdog_activation` and `test_provider_cooldown_failover` assert `spools/...` paths in `rig.fs.files`, a `FakeFileSystem` dictionary. The helper reads a real directory with `pathlib`, so it cannot read a fake filesystem; part 3 first needs a decision on how the helper reads a fake (an optional filesystem parameter, which is a signature change owned by that part). These two files stay out of this ticket.

Sites in this ticket, each routed with its fact kept (which file exists, what its text holds):

- `tests/integration/test_mergequeue.py` (6 sites: lines 363-365 `is_file` and `exists() == base_red` on `0/merge-integration/verify-01.txt` and `verify-01-base.txt`; line 389 asserts no `*.txt` under attempt 0; lines 411-412 assert the sorted `host-*` names `merge-integration/host-01.txt`, `merge-integration/host-03.txt`, `merge-safety/host-01.txt`; lines 457-458 read `4/merge-{name}/host-01.txt`; lines 832-833 read `0/merge-integration/verify-01.txt`).
- `tests/integration/test_merge.py` (line 533: the `*.txt` names under `spools/{stem}/{attempt}` contain `merge-integration/verify-01.txt`).
- `tests/integration/test_stages.py` (lines 482, 536 and 665: `check/verify-01-base.txt` `is_file`, and the text of `check/verify-02.txt`).
- `tests/integration/test_host_mechanical.py` (6 sites: `check/host-02.txt` exists; no `host-*` under attempt 0; the secret absent from `check/host-01.txt`; `merge/host-01.txt` exists; no file under `merge`; `check/host-01-rerun.txt` exists).
- `tests/integration/test_bug_gate.py` (line 336: the text of `merge-integration/regression-head.txt` and `regression-base.txt`).
- `tests/integration/test_daemon_composition.py` (line 1088: `7/merge-integration/verify-01.txt` is a file).
- `tests/integration/test_daemon_soak_runner.py` (line 192: the text of `semantic/0/merge-integration/verify-01.txt` and its use in `message.summary`; lines 265-266 and 270, 305: the tamper test reads and rewrites the two spool files `semantic/0/merge-integration/verify-01.txt` and `mechanical/0/merge-integration/verify-01.txt` by relative path, so those two entries read the original bytes with `read_capture` and write the replacement and the restore with `write_capture`, while the three non-spool entries of that dictionary keep their path and `member.fs.write`).
- `tests/integration/test_serve_admission.py` (6 sites: lines 155-157 text `exit 0` in three files of `work/1` attempt 1; lines 452-456 existence of `merge-integration/verify-01.txt` and `verify-01-base.txt` in `work/0`; line 566 text of `merge-{tier}/host-01.txt`).

The names `list_captures` returns are the names the caller passed to `Spool.write` (`merge-integration/verify-01.txt`), never a `run-` prefixed name, so a membership check on `[name for _, name in list_captures(state_dir, stem, attempt)]` states the same fact as today's `is_file()`. A text read is `read_capture(state_dir, stem, attempt, name).decode()`. A missing file raises `CaptureNotFound`, so a test that today asserts `is_file()` and then reads uses the read alone, and a test that asserts absence uses the listing.

Files read and left alone, with the reason: `tests/integration/test_kill_executor_abort.py` only passes `driver.spool.root.parent` as a workspace argument and asserts no spool path; `tests/integration/test_evidence_envelope.py` greps `clutch/` source and a docs table row for the text `spools/`, a path in a document, not a spool file; `tests/unit/` was routed by `spools-test-helper`.

## Boundary contract
### Routed integration spool assertions
- disposition: extend
- owner: the eight test files in Scope in
- consumers: the integration suite and, at the flip, `spools-onto-evidence-store-r2`
- observable change: each assertion reads spool files through `read_capture` or `list_captures` instead of a hand-built `spools/` path; the facts asserted (which files exist, their text) are unchanged and no assertion weakens
- compatibility: preserves the asserted facts; `tests/spool_captures.py`, its signatures and every production file are unchanged
- acceptance: criteria 1 to 4 below
- tests: tests/integration/test_mergequeue.py, tests/integration/test_merge.py, tests/integration/test_stages.py, tests/integration/test_host_mechanical.py, tests/integration/test_bug_gate.py, tests/integration/test_daemon_composition.py, tests/integration/test_daemon_soak_runner.py, tests/integration/test_serve_admission.py
- post-merge source of truth: tests/spool_captures.py for the `spools/` layout; the eight files for the routed facts

## Scope in / Scope out
Scope in:
- Route the sites listed in Goal in the eight fenced files through `tests/spool_captures.py`, plus the import each file needs. Nothing else in those files changes.
- No new test file: the helper has its own test, `tests/unit/test_spool_captures.py`, and this ticket adds no behavior; the routed assertions are the tests.
- A positive existence or text assertion becomes a `read_capture` call or a name-membership check on `list_captures`, with the stem, attempt and name the old path spelled. A negative assertion (`assert not list(...rglob(...))`, `not exists()`) becomes a listing filtered by the same prefix or suffix and asserted empty, with an exact-equality sibling or the positive assertions in the same test showing the listing is not vacuous where one exists.
- `tests/integration/test_daemon_soak_runner.py` line 192 is the only site where the text is also compared to `message.summary`; it keeps that comparison on the decoded text.

Scope out:
- All production code, docs and prompt specs, and `tests/spool_captures.py` itself (row 63 flips its body).
- Parts 2 and 3 above, and the two files left alone.
- Any change that makes the helper read a fake filesystem.
- Merge order: confirmed, unmerged tickets that also fence these files (`commit-lock`, `dispatch-during-driver-pass-gate`, `parallel-dispatch-run-context`, `merge-tree-check-ignores-ticket-plane`, `meta-annotate-tests-integration-a`, `meta-annotate-tests-integration-b`, `core-drift-preflight`, `eval-move-soak-battery-host-loop`, `merge-admission-single-owner`, `bug-evidence-before-dispatch`, `stages-base-worktree-helper`, `host-check-selection-single-owner`, `check-test-timing`, `serve-parallel-dispatch-r2`, `conflict-rerun-swap`, `move-serve-remaining-tests` and others) edit header lines or code elsewhere in these files; none is known to edit the `spools/` lines routed here, so either merge order leaves both applicable, and a mechanical rebase conflict at an import line is resolved by keeping both imports. `spools-onto-evidence-store-r2` is a draft that lists `spools-tests-via-helper` in the roadmap row and must also depend on parts 2 and 3 before it runs; it fences `tests/integration/test_driver.py`, which is part 2, not this ticket.
- `context-suggest-author-block` and `review-panel-stage-use` fence none of the eight files.

## Scope fence
- tests/integration/test_mergequeue.py
- tests/integration/test_merge.py
- tests/integration/test_stages.py
- tests/integration/test_host_mechanical.py
- tests/integration/test_bug_gate.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_daemon_soak_runner.py
- tests/integration/test_serve_admission.py

## Acceptance criteria
1. Single call site: `grep -n 'spools' tests/integration/test_mergequeue.py tests/integration/test_merge.py tests/integration/test_stages.py tests/integration/test_host_mechanical.py tests/integration/test_bug_gate.py tests/integration/test_daemon_composition.py tests/integration/test_daemon_soak_runner.py tests/integration/test_serve_admission.py` prints no line, not a line left over from an unrouted site; the `ctx.driver.spool._fs is ctx.fs` identity check in `test_daemon_composition.py` names `spool`, not `spools`, so it does not match and stays.
2. `./dev.py test tests/integration/test_mergequeue.py tests/integration/test_merge.py tests/integration/test_stages.py tests/integration/test_host_mechanical.py tests/integration/test_bug_gate.py` passes, with `test_verification_uses_rebased_worktree` still asserting `verify-01.txt` exists and `verify-01-base.txt` exists only when `base_red` is true, not that both exist always, and the `host-*` listing test still asserting exactly `merge-integration/host-01.txt`, `merge-integration/host-03.txt` and `merge-safety/host-01.txt`, not a superset.
3. `./dev.py test tests/integration/test_daemon_composition.py tests/integration/test_daemon_soak_runner.py tests/integration/test_serve_admission.py` passes, with the tamper test still failing closed (`pytest.raises((soak.SoakRefused, ValueError))`) for the `integration` and `regating` fields after the two spool files are rewritten with `write_capture`, and the original bytes restored with `write_capture`, not left as `{}`.
4. Every negative assertion routed (`test_queue_skips_unchanged_code`, `test_untriggered_entry_never_runs`, and the `merge` directory check in `test_host_mechanical.py`) filters `list_captures` by the same name prefix or suffix the old glob used and asserts the result is `[]`, not that `list_captures` is `[]` for the whole attempt, so an unrelated capture does not fail it; `git diff` shows no file outside the fence changed and no file under `clutch/` or `tests/spool_captures.py` changed, checked in review as a one-time check.

## Verification
```
./dev.py test tests/integration/test_mergequeue.py tests/integration/test_merge.py tests/integration/test_stages.py tests/integration/test_host_mechanical.py tests/integration/test_bug_gate.py tests/integration/test_daemon_composition.py tests/integration/test_daemon_soak_runner.py tests/integration/test_serve_admission.py
uv run ruff format --check .
```

## Definition of rejected
A production file, `tests/spool_captures.py`, a doc, or a file outside the fence changes; a routed assertion is weakened, deleted, or loosened to a superset; a test builds a `spools/` path or a second helper reads the layout; the helper is given a filesystem parameter or a second read path; a new test file or a new fixture is added to a hot file; or a SQLite file is opened.

## Time budget
- expected: 25m
- stuck: 50m
- reason: About 27 mechanical sites in 8 files, no new behavior; the five hot files' integration runs make Verification the slow part, and the remaining families are split into two more rows
