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
- clutch/merge.py
- clutch/mergequeue.py
- clutch/stages.py::served_review
- clutch/stages.py::gather_evidence
- clutch/stages.py::gather_safety_evidence
- clutch/artifacts.py::StageResult
- docs/roadmap.md
- tests/integration/test_daemon_tasks.py

## Goal / Why
Admission to main has one owner. Today `merge.merge` (inline, used by `run` and `drain`) and `MergeQueue._admit` (serve) each hold their own copy of the rebase, evidence, gate and refusal logic, and the copies differ. After this change `merge.merge` is a thin call into `MergeQueue._admit`. The differences between the two paths are parameters of `_admit`, not separate code. `gather_safety_evidence` runs once per admission: `gather_evidence` accepts the safety result it is given instead of gathering it again. There is one `refused` constructor, `artifacts.refused(findings, cost)`. `served_review` no longer returns `(None, None)` for every exception, because that nulls the receipt's provider and model on any defect. `merge-model-resolve` adds a resolve rung to `_admit`, and it needs one admission body to extend rather than two copies that can disagree. This is roadmap row 16; the duplication is rows 11 and 12 of the duplication table in `docs/roadmap.md`, and the swallow is in the table near `served_review`.

## Scope in / Scope out
Scope in:
- `merge.merge` keeps its signature `merge(ctx, ticket, *, attempt) -> StageResult`. Its body only builds the inline parameter set and calls `MergeQueue._admit`. No rebase, gate, evidence or squash code remains in it. Inline behavior is unchanged: same outcomes, findings and journal events as before, with no receipt written and no tree check.
- `MergeQueue._admit` takes every inline/serve difference as a keyword parameter whose default is the serve behavior, so `MergeQueue.dispatch` and existing serve-path test wrappers that call `_admit(ticket, attempt)` positionally (for example in `tests/integration/test_serve_admission.py`, `tests/integration/test_mergequeue.py` and `tests/integration/test_daemon_tasks.py`) keep working unchanged. The parameter set covers the five named variations (conflict-resolution ladder, safety tier, receipt, tree check, red streak) and also these further differences that merged code has today:
  - conflict-facts signalling: serve journals `merge_conflict_facts` through `_facts` on every path; inline journals none (guard: `tests/integration/test_merge.py` line 192 asserts inline writes none);
  - host-check selection and spool prefix: inline uses `triggered_hosts(..., hard_only=True)` and spools to `merge/host-NN.txt` (guard: `tests/integration/test_host_mechanical.py` line 106); serve uses `host_checks` (trigger `always` plus hard, or `merge.safety_checks`) and spools to `merge-safety/` or `merge-integration/`;
  - the gather stage name: inline passes `stage="merge"` to `gather_evidence`, serve passes `stage="merge-integration"`;
  - strategy scoping and receipt lookup: inline runs CHECK_GATES on unscoped evidence with no strategy-exemption findings and no HELD-receipt lookup; serve does both.
  The serve parameter set reproduces today's serve behavior exactly, the inline parameter set reproduces today's inline behavior exactly, and `MergeQueue.dispatch` and `AdmissionBoundary` keep working.
- `stages.gather_evidence` gains an optional keyword `safety: Evidence | None = None`. When it is given, `gather_evidence` does not call `gather_safety_evidence`. `_admit` passes the safety result it already holds. Other callers of `gather_evidence` are unchanged. This edit is forced into `tests/integration/test_stages.py` (the recording test near `gather_evidence ... attempt=4`) and into the trace expectations in `tests/integration/test_mergequeue.py`, `tests/integration/test_serve_admission.py` and `tests/integration/test_restart_timers.py`. The expected call lists lose their second `gather_safety_evidence`. Nothing else changes in those files.
- `tests/integration/test_bug_gate.py`: delete only the line (443) `monkeypatch.setattr(merge, "gather_evidence", without_custody)`, because `merge.py` no longer uses `gather_evidence` and the patch would raise AttributeError. The `stages.gather_evidence` patch on the line before it already covers `_admit`, which calls `stages.gather_evidence`. Nothing else changes in that file.
- `tests/integration/test_hostfiles.py` (`test_core_drift_reachable_from_production_gates`), forced because inline merge now delegates to `_admit`:
  - delete line 330 `monkeypatch.setattr(merge, "run_gates", observe)`, because `merge.py` no longer imports `run_gates` and the patch would raise AttributeError; the `queue_module.run_gates` patch at line 333 already covers `_admit`;
  - change the `queued_admit(queue, ticket, attempt)` wrapper at line 350 to accept `**kwargs` and forward them to `original_admit`, so the inline parameter set reaches the real `_admit`;
  - the inline wrapper at lines 342-344 already moves main, so the inline path through `queued_admit` must not call `move_main` a second time (for example, the inline wrapper sets `moved = True` after its `move_main`).
  Nothing else changes in that file.
- Add `refused(findings, cost, artifact=None) -> StageResult` to `clutch/artifacts.py`. Delete `merge._refused` and the `refused` closure in `_admit`. Replace the inline `StageResult(outcome="gate_failed", ...)` constructions at `runner.py` (the findings re-wrap in the stage result handler), `stages.py` (the three in the Check/Review gate path and the one in the stage-run loop) and `daemon.py` (the three in the Rework path) with calls to it.
- `served_review` keeps its explicit "not attested" returns of `(None, None)` (no unique review lift, lift not an ancestor of main, review not an approval for this sha, no LLM call event, verdict mismatch). It drops the blanket `except ValueError, KeyError, TypeError, AttributeError, GitError`, so a malformed verdict, a git failure or a malformed event body propagates to the caller.
- Update the sentence about inline merge in `docs/how-clutch-works.md` (section naming `merge.merge`) to say it is a thin call into the queue's admission.
- New unit tests in `tests/unit/test_merge_admission_params.py` run the new lines in the floored files (`clutch/mergequeue.py`, `clutch/merge.py`, `clutch/stages.py`, `clutch/runner.py`, `clutch/daemon.py`) with in-memory fakes for `ctx.git`, `ctx.exec_`, `ctx.fs` and the journal, with no repo files or processes. The seams are the injectable ones `_admit` already reads from `ctx` plus the new `safety` keyword and the `_admit` parameters. The real-git checks stay in `tests/integration/test_merge_admission_owner.py`.
- Before committing, run the full `./dev.py test`: tests that monkeypatch `merge.*` names or wrap `_admit` (grep `tests/` for `_admit` and `setattr(merge`) surface only in the full suite.
Scope out: `stages._short` (it rewrites an existing result's outcome, a different operation), `rework.py`, the merge strategies and conflict-handoff behavior, any new resolve rung, and `docs/roadmap.md` (the engine strikes rows).

## Scope fence
- clutch/merge.py
- clutch/mergequeue.py
- clutch/stages.py
- clutch/artifacts.py
- clutch/runner.py
- clutch/daemon.py
- docs/how-clutch-works.md
- tests/integration/test_stages.py
- tests/integration/test_mergequeue.py
- tests/integration/test_serve_admission.py
- tests/integration/test_restart_timers.py
- tests/integration/test_bug_gate.py
- tests/integration/test_hostfiles.py
- tests/integration/test_merge_admission_owner.py
- tests/unit/test_artifacts_refused.py
- tests/unit/test_merge_admission_params.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_merge_admission_owner.py` includes a test that runs `merge.merge` on a reviewed branch with `stages.gather_safety_evidence` wrapped by a counter. It asserts the counter is exactly 1 (not 2) and that the result outcome is `ok`. A second test does the same through `MergeQueue._admit` and asserts exactly 1.
2. The same file asserts `merge.merge` and `MergeQueue._admit` both reach the same function: with `MergeQueue._admit` monkeypatched to return a sentinel `StageResult`, `merge.merge` returns that sentinel. A `merge.merge` that still carries its own body returns a real result instead.
3. The existing inline merge tests (`tests/integration/test_merge.py`, `tests/integration/test_host_mechanical.py`) pass unchanged, `tests/integration/test_bug_gate.py` passes with only the `merge.gather_evidence` patch line removed, and `tests/integration/test_hostfiles.py` passes with only the `merge.run_gates` patch removed and the `queued_admit` wrapper forwarding keyword parameters without moving main twice. This includes the refusal cases: a conflicted rebase, a dirty overlap and a red hard check each yield `gate_failed` with main untouched, inline merge journals no `merge_conflict_facts` (test_merge.py), and inline hard host checks spool to `merge/host-NN.txt` (test_host_mechanical.py). This shows inline outcomes are the same, not just that the call is forwarded.
4. `tests/unit/test_artifacts_refused.py` asserts `refused([f], Cost(seconds=2))` returns `outcome == "gate_failed"`, `artifact is None`, `findings == [f]` and `cost.seconds == 2`, and that passing `artifact=x` keeps `x` (not `None`).
5. `grep -rn "_refused\|outcome=\"gate_failed\"" clutch/merge.py clutch/mergequeue.py clutch/runner.py clutch/daemon.py clutch/stages.py` shows no `StageResult(outcome="gate_failed"` construction and no `_refused` definition outside `artifacts.refused`. `stages._short` is the only remaining producer of that outcome.
6. A test in `tests/integration/test_merge_admission_owner.py` makes the review record's verdict JSON unparseable and asserts `served_review` raises (it does not return `(None, None)`). A second test with no review lift asserts it still returns `(None, None)`.
7. The serve trace in `tests/integration/test_mergequeue.py` and `tests/integration/test_serve_admission.py` equals `["restore", "rebase_stop_at_conflict", "gather_safety_evidence", "gather_evidence", "merge_squash"]` and its sibling lists, each with one `gather_safety_evidence`, not two.
8. `tests/unit/test_merge_admission_params.py` runs with fakes and no repo file or process: one test calls `gather_evidence(..., safety=<Evidence>)` and asserts `gather_safety_evidence` is called 0 times (not 1) and the given Evidence is the one used; one test drives `_admit` with the inline parameter set and asserts no `merge_conflict_facts` event is journaled and the gather stage is `"merge"`; one test drives `_admit` with the serve parameter set and asserts the stage is `"merge-integration"` and `merge_conflict_facts` is journaled on a conflict.
9. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/integration/test_merge_admission_owner.py tests/unit/test_artifacts_refused.py tests/unit/test_merge_admission_params.py tests/integration/test_merge.py tests/integration/test_mergequeue.py tests/integration/test_serve_admission.py tests/integration/test_restart_timers.py tests/integration/test_stages.py tests/integration/test_host_mechanical.py tests/integration/test_bug_gate.py tests/integration/test_hostfiles.py tests/integration/test_daemon_tasks.py
./dev.py test
```

## Definition of rejected
The branch is rejected if `merge.merge` keeps its own rebase, gate or squash body, if any path still gathers safety evidence twice, if a second refused constructor remains in the files named in criterion 5, if `served_review` still catches the broad exception tuple, or if inline or serve outcomes change for an existing passing test.

## Time budget
- expected: 60m
- stuck: 120m