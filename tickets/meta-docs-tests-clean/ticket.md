---
state: draft
source: human
priority: P1
kind: chore
---

## Depends on
- meta-schema-and-refresh-r2

## Context
- clutch/meta.py::check
- clutch/meta.py::refresh
- clutch/meta.py::generated

## Goal / Why
Roadmap row 207 (`meta-context-ship-gate`), part 1 of 2. The roadmap section 1 0.5.0 ship clause wants this repo's docs and tests to carry filled meta blocks. Measured 2026-11-21 13:55Z, `uv run clutch meta check docs clutch/docs tests` exits 1 with 29 findings, one file each: 16 `missing` (no block), 7 `drifted` (block hash differs from the body), 6 `empty_purpose`. The row's "six files with an empty purpose" misses the other 23. After this ticket none of those 29 files has a finding, so the gate command the next ticket adds can pass. Run `uv run clutch meta check` with the 29 paths to get the live list; the fence below is that list.

Fix, in order: (1) `uv run clutch meta refresh <the 29 paths>` inserts blocks into the missing files and restamps drifted hashes; (2) edit only the `purpose:` line of every file whose purpose is empty after refresh (the 16 refreshed-new files and the 6 empty ones) to one short phrase saying what that file tests or holds, written from reading the file; (3) for each of the 7 drifted files, re-read the existing `purpose` against the body and fix it if false. No model call: do not run `meta fill`. Do not change any line outside the meta block. This is 29 files but a diff of about 10 lines each (under 400 inserted lines), so it is one ticket, not shards.

## Boundary contract
none
- reason: metadata only; only clutch:meta header blocks change and no code, test body, or document text changes.

## Scope in / Scope out
In: the meta block of each fenced file, by the three steps above. `docs/roadmap.md` gets only its block restamped; no row or heading text changes.
Out: `meta fill`, any code change, new test files, files that gain a finding after this ticket was written (a later drift is the next ticket's or the owner's), the 0.5.0 gate block (`meta-context-ship-gate`).

## Scope fence
- docs/roadmap.md
- tests/integration/test_ask_plan_conduct_covered.py
- tests/integration/test_closed_sets.py
- tests/integration/test_diagnose_spec_engine_cause.py
- tests/integration/test_evidence_verbs.py
- tests/integration/test_gates.py
- tests/integration/test_implement_spec_meta_headers.py
- tests/integration/test_mergequeue_tree_moved.py
- tests/integration/test_meta_fill_spec.py
- tests/integration/test_repo_requisition_sonnet.py
- tests/integration/test_testguard.py
- tests/regress_sleep_skew/sitecustomize.py
- tests/regress_testguard_slowest_load.py
- tests/unit/test_evidence_normalized_store.py
- tests/unit/test_evidence_views.py
- tests/unit/test_git_ticket_touches.py
- tests/unit/test_images_gate.py
- tests/unit/test_index_config.py
- tests/unit/test_main_evidence_captures.py
- tests/unit/test_main_evidence_group.py
- tests/unit/test_main_meta_fill.py
- tests/unit/test_main_meta_group.py
- tests/unit/test_mergequeue_tree_check.py
- tests/unit/test_meta_drift_check.py
- tests/unit/test_meta_drift_gate.py
- tests/unit/test_meta_fill.py
- tests/unit/test_review_panel_dropped_findings.py
- tests/unit/test_scratch_dir_paths.py
- tests/unit/test_stages_candidates_select.py

## Acceptance criteria
1. Every one of the 29 fenced files has a filled meta block: `uv run clutch meta check docs/roadmap.md tests/integration/test_ask_plan_conduct_covered.py tests/integration/test_closed_sets.py tests/integration/test_diagnose_spec_engine_cause.py tests/integration/test_evidence_verbs.py tests/integration/test_gates.py tests/integration/test_implement_spec_meta_headers.py tests/integration/test_mergequeue_tree_moved.py tests/integration/test_meta_fill_spec.py tests/integration/test_repo_requisition_sonnet.py tests/integration/test_testguard.py tests/regress_sleep_skew/sitecustomize.py tests/regress_testguard_slowest_load.py tests/unit/test_evidence_normalized_store.py tests/unit/test_evidence_views.py tests/unit/test_git_ticket_touches.py tests/unit/test_images_gate.py tests/unit/test_index_config.py tests/unit/test_main_evidence_captures.py tests/unit/test_main_evidence_group.py tests/unit/test_main_meta_fill.py tests/unit/test_main_meta_group.py tests/unit/test_mergequeue_tree_check.py tests/unit/test_meta_drift_check.py tests/unit/test_meta_drift_gate.py tests/unit/test_meta_fill.py tests/unit/test_review_panel_dropped_findings.py tests/unit/test_scratch_dir_paths.py tests/unit/test_stages_candidates_select.py` exits 0, not 1 (it prints no `missing`, `drifted` or `empty_purpose` line).
2. No fenced file's text changes outside its meta block: `git diff --stat` on the branch shows only those paths and a reviewer reads each hunk inside the block header (checked in review).
3. Fenced Python files still import and the tests among them still pass: `./dev.py test tests/unit/test_images_gate.py tests/integration/test_closed_sets.py tests/integration/test_gates.py` exits 0.

## Verification
```
uv run clutch meta check docs/roadmap.md tests/integration/test_ask_plan_conduct_covered.py tests/integration/test_closed_sets.py tests/integration/test_diagnose_spec_engine_cause.py tests/integration/test_evidence_verbs.py tests/integration/test_gates.py tests/integration/test_implement_spec_meta_headers.py tests/integration/test_mergequeue_tree_moved.py tests/integration/test_meta_fill_spec.py tests/integration/test_repo_requisition_sonnet.py tests/integration/test_testguard.py tests/regress_sleep_skew/sitecustomize.py tests/regress_testguard_slowest_load.py tests/unit/test_evidence_normalized_store.py tests/unit/test_evidence_views.py tests/unit/test_git_ticket_touches.py tests/unit/test_images_gate.py tests/unit/test_index_config.py tests/unit/test_main_evidence_captures.py tests/unit/test_main_evidence_group.py tests/unit/test_main_meta_fill.py tests/unit/test_main_meta_group.py tests/unit/test_mergequeue_tree_check.py tests/unit/test_meta_drift_check.py tests/unit/test_meta_drift_gate.py tests/unit/test_meta_fill.py tests/unit/test_review_panel_dropped_findings.py tests/unit/test_scratch_dir_paths.py tests/unit/test_stages_candidates_select.py
./dev.py test tests/unit/test_images_gate.py tests/integration/test_closed_sets.py tests/integration/test_gates.py
```

## Definition of rejected
A purpose copied from a sibling file without reading the file, a text change outside a meta block, a fenced path left with a finding, or any edit outside the fence.

## Time budget
- expected: 15m
- stuck: 30m
