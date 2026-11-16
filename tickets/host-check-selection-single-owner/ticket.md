---
state: confirmed
source: box:roadmap_row
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
- merge-admission-single-owner

## Context
- clutch/stages.py::triggered_hosts
- clutch/stages.py::run_host_command
- clutch/stages.py::check_hosts
- clutch/mergequeue.py::MergeQueue.host_checks
- docs/roadmap.md#2.1 Engine core

## On-demand
- clutch/merge.py
- tests/integration/test_host_mechanical.py

## Goal / Why
Roadmap row 17 (duplication-table rows 3 and 4, plus the swallow row for the coverage parse and base `results` read). Host-check selection and execution each have more than one owner today:

- Three filters pick `review.mechanical` entries: `stages.triggered_hosts` (Check, all triggered; merge, triggered and hard via `hard_only=True`), and the integration and safety selections inside `MergeQueue.host_checks`.
- `gather_evidence` runs the Verification loop and its base rerun loop with its own copy of the run-argv, stuck-budget, spool and tail code that `run_host_command` already holds.
- `_check_host_results` swallows an unreadable coverage report (`except ...: pass`, so `TestCoverage` is silently absent), and `check_hosts` reads the base `results` file and discards it.

After this change `triggered_hosts(ctx, changed_files, *, tier)` is the one filter and `run_host_command` is the one runner for Check, Verification and the merge tiers. A declared coverage report that is missing or invalid on a passing run fails with a finding instead of vanishing, and the discarded base `results` read is gone. `serve-parallel-dispatch` needs one runner to put the engine-wide host-command lock around, and one filter so Check and both merge tiers cannot disagree about which entries run.

Ordering: `merge-admission-single-owner` moves the inline merge selection (`hard_only=True` plus the `merge/host-NN` spool) out of `merge.merge` into a parameter of `MergeQueue._admit`. This ticket depends on it so the call sites below are edited where they live after that move.

## Scope in / Scope out
Scope in:
- `clutch/stages.py::triggered_hosts` replaces `hard_only` with a required keyword `tier`, a closed set: `check` (every entry whose trigger fires), `merge` (triggered and `severity == hard`, the inline merge-admission selection), `integration` (`trigger == "always"` and hard, the queue's integration tier), `safety` (the hard entries named in `merge.safety_checks`, each code resolving to exactly one hard entry). An unknown tier raises `ValueError`. `integration` and `safety` do not read `changed_files`. Entries keep their 1-based position `n` in `review.mechanical`.
- Call sites: `check_hosts` uses `tier="check"`; every other caller of `triggered_hosts`, wherever the inline merge selection lives (`clutch/merge.py` or `MergeQueue._admit`), passes `tier="merge"`; `MergeQueue.host_checks` selects through `triggered_hosts` with `tier="safety"` or `"integration"` instead of its own list comprehensions. `host_checks` keeps building the failure report for a `merge.safety_checks` code that does not resolve to exactly one hard entry; that is a finding, not a filter.
- `gather_evidence` runs each Verification argv and each base rerun through `run_host_command` (default cwd for the branch run, `cwd=base_worktree` for the rerun). Spool names stay `{stage}/verify-NN.txt` and `{stage}/verify-NN-base.txt`; the `base_red` logic is unchanged. These are replaced lines; the existing integration tests in `tests/integration/test_host_mechanical.py` cover them, and no new unit test drives `gather_evidence`.
- `_check_host_results`: when `entry.coverage` is declared and the report is missing or invalid (`OSError`, `UnicodeError`, `ValueError`) and the command exited 0, return a failing report with one `Finding` (code `entry.code`, path `entry.coverage`, message `Missing or invalid coverage report: <path>`, paved road naming `--cov-report=json:<path>`). A nonzero exit still records no coverage and adds no finding, because the failing command already fails the report.
- `check_hosts`: delete the base `results` read (`read_results` call, its import, and its `except`) and the `ctx.fs.remove(base_worktree / entry.results)` that only prepared it.
- `docs/how-clutch-works.md`: edit only the sentence "All use one shared command runner" in the host-check paragraph so it also says one filter, `triggered_hosts(tier=...)`, selects the entries for Check and both merge tiers.
- `tests/integration/test_host_mechanical.py::test_coverage_recorded_for_changed_files`: the invalid-coverage case now expects verdict `fail` with the finding above instead of `pass` with `coverage` None. That is the one expectation that may change there.
- `tests/unit/test_host_check_selection.py` (new) runs the new lines with fakes and `tmp_path` only: `triggered_hosts` per tier; `_check_host_results` with a fake ctx whose `worktree()` returns `tmp_path` and fake exec, spool, clock, redactor and journal; and `MergeQueue.host_checks` with a fake ctx and a patched `_command`.

Scope out:
- Spool names for host entries (`check/host-NN`, `merge/host-NN`, `merge-<tier>/host-NN`) do not change.
- `MergeQueue._command` stays (tests patch it). `_gather_bug.execute` stays: it needs raw stdout and its own `OSError` handling, which `run_host_command` does not return.
- `tests/integration/test_mergequeue.py` and `tests/integration/test_host_contract.py` are not edited; they run unchanged as verification.
- The host-command lock belongs to `serve-parallel-dispatch`. The coverage-contexts error return, flake logic and autofix path are untouched.

## Scope fence
- clutch/stages.py
- clutch/merge.py
- clutch/mergequeue.py
- docs/how-clutch-works.md
- tests/unit/test_host_check_selection.py
- tests/integration/test_host_mechanical.py

## Acceptance criteria
1. `tests/unit/test_host_check_selection.py` calls `triggered_hosts` with fake entries for each tier: `check` returns an unhardened entry whose trigger fires and omits one whose trigger does not; `merge` omits a triggered soft entry that `check` returns; `integration` returns only always+hard entries and not a path-triggered hard entry; `safety` returns only the entry named in `merge.safety_checks`, not another hard entry. Each returns the entry's 1-based position in `review.mechanical`, not a list index.
2. `triggered_hosts(ctx, [], tier="bogus")` raises `ValueError`, and the old `hard_only` keyword is a `TypeError` (`pytest.raises` in the same unit test).
3. `grep -n "hard_only" clutch` prints nothing, and `MergeQueue.host_checks` contains no `enumerate(self.ctx.config.review.mechanical` selection of its own.
4. `tests/unit/test_host_check_selection.py` calls `_check_host_results` with a fake ctx, an exit-0 result and an invalid coverage file under `tmp_path`, and asserts a failing report with a `Missing or invalid coverage report` finding, not a passing report with `coverage` None; with a nonzero exit it asserts no such finding is added.
5. `tests/unit/test_host_check_selection.py` calls `MergeQueue.host_checks` with a fake ctx and patched `_command`, and asserts which entries run for `safety` and for `integration`, and that a `merge.safety_checks` code resolving to no hard entry yields the failure report rather than a run.
6. `tests/integration/test_mergequeue.py` and `tests/integration/test_host_contract.py` pass unchanged: the safety/integration spool names and the unresolved-designation failure report are as before.
7. `test_coverage_recorded_for_changed_files[False]` asserts `report.verdict == "fail"` and a finding whose message contains `Missing or invalid coverage report`, not `pass` with `coverage` None; the `[True]` case still records `{"percent": 75.0, "files": {"changed.py": 50.0}}`.
8. `grep -n "read_results" clutch/stages.py` shows no use inside `check_hosts`, and `gather_evidence` contains no direct `ctx.exec_.run` call (`grep -c` of that string inside the function is 0).
9. The Verification spool files `check/verify-01.txt` and `check/verify-01-base.txt` are still written with the same `$ argv`/`[exit]` layout (covered by the existing `tests/integration/test_host_mechanical.py` tests passing unchanged apart from criterion 7).

## Verification
```
./dev.py test tests/unit/test_host_check_selection.py tests/unit/test_check_timing.py tests/integration/test_host_mechanical.py tests/integration/test_mergequeue.py tests/integration/test_host_contract.py
```

## Definition of rejected
A second filter or a second argv runner survives for Check, Verification or either merge tier; any spool name changes; the invalid-coverage case still passes with coverage silently None on a zero exit; or the change adds a lock, a knob or a compatibility path for `hard_only`.

## Time budget
- expected: 55m
- stuck: 100m
