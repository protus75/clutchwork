---
state: confirmed
source: human
priority: P2
kind: chore
---

## Depends on
- meta-schema-and-refresh-r2
- evidence-verbs

## Context
- docs/annotations-index-plan.md

## Goal / Why
`meta-schema-and-refresh-r2` ships `clutch meta refresh` and `clutch meta check` and the `meta.paths` roots in `config.yaml`. After this ticket the 133 tracked `.md` and `.py` files in `docs/`, `clutch/docs/` and the files of `tests/` outside `tests/unit/` and `tests/integration/` each carry a valid `clutch.meta/1.0` block (after the closing frontmatter fence, or after the module docstring for Python), so `uv run clutch meta check` on exactly those files exits 0.

Why: the first attempt at `meta-schema-and-refresh-r2` annotated about 600 files in one diff of 5512 inserted lines and failed the 1500-line diff budget (`diagnosis.json`, verdict split). This ticket is one shard of that work, sized under the budget at about 9 inserted lines per file, so it can merge.

## Boundary contract
none
- reason: metadata only; each file gains a comment block produced by the unchanged `clutch meta refresh`, and no behavior, parser or consumer changes. The real readers are harmless: `clutch/author.py` copies `clutch/docs/host-authoring.md` into the Author prompt and `tests/integration/test_author.py` pins that copy, so the prompt gains the block as passed-through data; `clutch/roadmap.py` parses `docs/roadmap.md` and skips lines outside its tables, so the block does not parse as a row, and its hash drifts when a roadmap verb later rewrites the file, which no gate checks yet; the other `clutch/docs/*.md` files are shipped host guides that carry the block as an HTML comment

## Scope in / Scope out
In: Block placement is verified against the format gate. `ruff format` requires a blank line between a module docstring and the next code, and the original blank line stays there: refresh inserts the block right after the docstring, so the file reads docstring, `# clutch:meta` block, the original blank line, then code. Checked 2026-11-20 with ruff 0.17.3: `ruff format --diff` on exactly that shape (a docstring line, the eight block lines, one blank line, `import os`) reports `1 file already formatted`, and ruff reformats only the shape with no blank line after the comment (docstring, comment, `import os`), which a tracked file cannot have because it is already `ruff format`-clean. So `parse` still finds the block at the offset after the docstring, and `clutch/meta.py` needs no change. `uv run ruff format --check` over the shard's `.py` files is part of `## Verification` so this holds for every file. Then run `uv run clutch meta refresh` on exactly the files listed in `## Scope fence`, then give each block a non-empty `purpose`, because refresh inserts it empty and `meta check` reports `empty_purpose` for that. `meta fill` does not exist and is out of scope, so purposes are set with a throwaway script that is not committed and not fenced. Purpose rule, applied to every file the same way: for a `.py` file, the first line of its module docstring, else the file stem with `_` and `-` replaced by spaces; for a `.md` file, the text of its first `#` heading, else the file stem with `-` replaced by spaces; cut to at most 120 characters and never empty. Do not edit `relates`, `owner`, `kind`, `verified` or `hash` by hand. `docs/annotations-index-plan.md` takes only its own block: no other line of it changes. Refresh keeps every generated `# relates:` line within the line length that `meta-schema-and-refresh-r2` fixes, so no lint exemption is added and `pyproject.toml` is not touched. A file that fails `ruff` or an existing test only because of its new block is fixed in the block, never by editing the file's body.

Out: every other file, `clutch/specs/`, `meta fill`, the `meta_drift` gate, Check-time refresh, and any change to `config.yaml` (the roots are set by `meta-schema-and-refresh-r2`).

## Scope fence
- docs/
- clutch/docs/
- tests/__init__.py
- tests/approval.py
- tests/conftest.py
- tests/dispatch_settle.py
- tests/evidence_records.py
- tests/fakes.py
- tests/fixtures/evidence/claude/README.md
- tests/fixtures/evidence/codex/README.md
- tests/fixtures/evidence/gemini/README.md
- tests/harness/__init__.py
- tests/harness/daemon_soak.py
- tests/harness/host_loop.py
- tests/harness/reliability_battery.py
- tests/harness/shakeout/__init__.py
- tests/harness/shakeout/bench.py
- tests/harness/shakeout/drain.py
- tests/harness/shakeout/driver.py
- tests/harness/shakeout/merge.py
- tests/harness/shakeout/providers.py
- tests/harness/shakeout/recovery.py
- tests/harness/shakeout/run.py
- tests/harness/shakeout/runner.py
- tests/harness/shakeout/stages.py
- tests/regress_already_satisfied.py
- tests/regress_author_gate_own_draft_stem.py
- tests/regress_author_open_tickets_deleted.py
- tests/regress_base_red_branch_only_path.py
- tests/regress_bug_evidence_before_dispatch.py
- tests/regress_closed_sets_follow_up_row.py
- tests/regress_context_binary.py
- tests/regress_context_directory.py
- tests/regress_dev_test_args.py
- tests/regress_drain_containment.py
- tests/regress_drain_deadline.py
- tests/regress_drain_detach.py
- tests/regress_drain_park_findings.py
- tests/regress_drain_settles_admissions.py
- tests/regress_drain_signals.py
- tests/regress_engine_flag_only_drain_serve.py
- tests/regress_engine_text_verbs.py
- tests/regress_evidence_scoped_call_key.py
- tests/regress_graph_dependency_edges.py
- tests/regress_graph_lanes.py
- tests/regress_implement_incomplete.py
- tests/regress_implement_premise_path.py
- tests/regress_install_docs_name.py
- tests/regress_journal_incremental_read.py
- tests/regress_lint_carries.py
- tests/regress_lint_stuck_ceiling.py
- tests/regress_lint_worktree_journal.py
- tests/regress_new_skeleton_draft.py
- tests/regress_peak_memory_big_worker.py
- tests/regress_phase_step_kinds.py
- tests/regress_premise_overruled_escalates.py
- tests/regress_premise_park_keep.py
- tests/regress_provider_capture_overwrite.py
- tests/regress_provider_install_broken_binary.py
- tests/regress_reject_invalid_ticket.py
- tests/regress_reoffer_infra_retry.py
- tests/regress_requisition_events_owner_stem.py
- tests/regress_requisition_park_not_attempt.py
- tests/regress_requisition_prior_review.py
- tests/regress_requisition_stage_events.py
- tests/regress_retro_reemit_skip.py
- tests/regress_review_intakes_own_stem.py
- tests/regress_review_menu_committed_unlocked.py
- tests/regress_serve_reoffer_dispatch.py
- tests/regress_serve_reoffer_rule.py
- tests/regress_shared_hold_rule.py
- tests/regress_snapshot_latency.py
- tests/regress_snapshot_verdict_menu_parity.py
- tests/regress_stale_running.py
- tests/regress_status_optional_locks.py
- tests/regress_status_retires_settled_rows.py
- tests/regress_step_kind_icons.py
- tests/regress_suggest_lands_in_box.py
- tests/regress_triage_author_invoked_boundary.py
- tests/regress_verdict_decisions_retire_on_resolution.py
- tests/regress_verdict_submitted_message.py
- tests/regress_vscode_task_identity.py
- tests/regress_watch_surface_tier_truth.py
- tests/regress_watch_tests_fixture_repo.py
- tests/snapshot_scale_fixture.py
- tests/waiting.py

## Acceptance criteria
1. Each of the 133 files in `## Scope fence` carries a valid block with a matching hash and a non-empty `purpose`, so `uv run clutch meta check` on those files exits 0 with no `missing`, `empty_purpose`, `drifted` or `malformed` finding, not just a pass because it was given an empty list. Check: `uv run clutch meta check` over the same paths as `## Verification`.
2. The diff inserts fewer than 1500 lines, checked by the Check stage's `diff_budget` gate, and deletes none, checked once at review with `git diff --numstat` against the base showing 0 deleted lines for every file.
3. No file outside `## Scope fence` changes, checked by the Check stage's scope fence gate, and every `.md` file that began with `---` still does, checked once at review by reading the first line of each changed `.md` file in `git diff`.

## Verification
```
uv run clutch meta check clutch/docs/host-authoring.md clutch/docs/host-contract.md clutch/docs/host-gemini.md clutch/docs/host-qwen.md clutch/docs/host-running.md clutch/docs/host-training.md docs/annotations-index-plan.md docs/boundary-contract-plan.md docs/document-agent/audience/ai.md docs/document-agent/audience/developer.md docs/document-agent/audience/non-technical.md docs/document-agent/audience/student.md docs/document-agent/audience/technical.md docs/document-agent/audience/user.md docs/document-agent/format/html.md docs/document-agent/format/markdown.md docs/document-agent/format/pdf.md docs/document-agent/plan.md docs/document-agent/review/AutomatableReview.md docs/document-agent/review/BuildItReview.md docs/document-agent/review/CompressionReview.md docs/document-agent/review/CutReview.md docs/document-agent/review/KillReview.md docs/document-agent/review/evidence/OutcomeReview.md docs/document-agent/review/evidence/SeedPlanDiagnosis.md docs/document-agent/theme/dark.md docs/document-agent/theme/light.md docs/document-agent/tone/default.md docs/document-agent/tone/examples.md docs/document-agent/type/api.md docs/document-agent/type/architecture.md docs/document-agent/type/blog.md docs/document-agent/type/overview.md docs/document-agent/type/plan.md docs/document-agent/type/release-notes.md docs/document-agent/type/seed.md docs/document-agent/type/spec.md docs/document-agent/type/whitepaper.md docs/evidence-trail-plan.md docs/gemini-graphics-refactor-plan.md docs/how-clutch-works.md docs/journal-sql-refactor-plan.md docs/mcp-server-notes.md docs/parallel-tickets-plan.md docs/roadmap-driver-plan.md docs/roadmap.md docs/stage-panels-plan.md docs/training-data-plan.md docs/upstream-issue-plan.md tests/__init__.py tests/approval.py tests/conftest.py tests/dispatch_settle.py tests/evidence_records.py tests/fakes.py tests/fixtures/evidence/claude/README.md tests/fixtures/evidence/codex/README.md tests/fixtures/evidence/gemini/README.md tests/harness/__init__.py tests/harness/daemon_soak.py tests/harness/host_loop.py tests/harness/reliability_battery.py tests/harness/shakeout/__init__.py tests/harness/shakeout/bench.py tests/harness/shakeout/drain.py tests/harness/shakeout/driver.py tests/harness/shakeout/merge.py tests/harness/shakeout/providers.py tests/harness/shakeout/recovery.py tests/harness/shakeout/run.py tests/harness/shakeout/runner.py tests/harness/shakeout/stages.py tests/regress_already_satisfied.py tests/regress_author_gate_own_draft_stem.py tests/regress_author_open_tickets_deleted.py tests/regress_base_red_branch_only_path.py tests/regress_bug_evidence_before_dispatch.py tests/regress_closed_sets_follow_up_row.py tests/regress_context_binary.py tests/regress_context_directory.py tests/regress_dev_test_args.py tests/regress_drain_containment.py tests/regress_drain_deadline.py tests/regress_drain_detach.py tests/regress_drain_park_findings.py tests/regress_drain_settles_admissions.py tests/regress_drain_signals.py tests/regress_engine_flag_only_drain_serve.py tests/regress_engine_text_verbs.py tests/regress_evidence_scoped_call_key.py tests/regress_graph_dependency_edges.py tests/regress_graph_lanes.py tests/regress_implement_incomplete.py tests/regress_implement_premise_path.py tests/regress_install_docs_name.py tests/regress_journal_incremental_read.py tests/regress_lint_carries.py tests/regress_lint_stuck_ceiling.py tests/regress_lint_worktree_journal.py tests/regress_new_skeleton_draft.py tests/regress_peak_memory_big_worker.py tests/regress_phase_step_kinds.py tests/regress_premise_overruled_escalates.py tests/regress_premise_park_keep.py tests/regress_provider_capture_overwrite.py tests/regress_provider_install_broken_binary.py tests/regress_reject_invalid_ticket.py tests/regress_reoffer_infra_retry.py tests/regress_requisition_events_owner_stem.py tests/regress_requisition_park_not_attempt.py tests/regress_requisition_prior_review.py tests/regress_requisition_stage_events.py tests/regress_retro_reemit_skip.py tests/regress_review_intakes_own_stem.py tests/regress_review_menu_committed_unlocked.py tests/regress_serve_reoffer_dispatch.py tests/regress_serve_reoffer_rule.py tests/regress_shared_hold_rule.py tests/regress_snapshot_latency.py tests/regress_snapshot_verdict_menu_parity.py tests/regress_stale_running.py tests/regress_status_optional_locks.py tests/regress_status_retires_settled_rows.py tests/regress_step_kind_icons.py tests/regress_suggest_lands_in_box.py tests/regress_triage_author_invoked_boundary.py tests/regress_verdict_decisions_retire_on_resolution.py tests/regress_verdict_submitted_message.py tests/regress_vscode_task_identity.py tests/regress_watch_surface_tier_truth.py tests/regress_watch_tests_fixture_repo.py tests/snapshot_scale_fixture.py tests/waiting.py
uv run ruff format --check tests/__init__.py tests/approval.py tests/conftest.py tests/dispatch_settle.py tests/evidence_records.py tests/fakes.py tests/harness/__init__.py tests/harness/daemon_soak.py tests/harness/host_loop.py tests/harness/reliability_battery.py tests/harness/shakeout/__init__.py tests/harness/shakeout/bench.py tests/harness/shakeout/drain.py tests/harness/shakeout/driver.py tests/harness/shakeout/merge.py tests/harness/shakeout/providers.py tests/harness/shakeout/recovery.py tests/harness/shakeout/run.py tests/harness/shakeout/runner.py tests/harness/shakeout/stages.py tests/regress_already_satisfied.py tests/regress_author_gate_own_draft_stem.py tests/regress_author_open_tickets_deleted.py tests/regress_base_red_branch_only_path.py tests/regress_bug_evidence_before_dispatch.py tests/regress_closed_sets_follow_up_row.py tests/regress_context_binary.py tests/regress_context_directory.py tests/regress_dev_test_args.py tests/regress_drain_containment.py tests/regress_drain_deadline.py tests/regress_drain_detach.py tests/regress_drain_park_findings.py tests/regress_drain_settles_admissions.py tests/regress_drain_signals.py tests/regress_engine_flag_only_drain_serve.py tests/regress_engine_text_verbs.py tests/regress_evidence_scoped_call_key.py tests/regress_graph_dependency_edges.py tests/regress_graph_lanes.py tests/regress_implement_incomplete.py tests/regress_implement_premise_path.py tests/regress_install_docs_name.py tests/regress_journal_incremental_read.py tests/regress_lint_carries.py tests/regress_lint_stuck_ceiling.py tests/regress_lint_worktree_journal.py tests/regress_new_skeleton_draft.py tests/regress_peak_memory_big_worker.py tests/regress_phase_step_kinds.py tests/regress_premise_overruled_escalates.py tests/regress_premise_park_keep.py tests/regress_provider_capture_overwrite.py tests/regress_provider_install_broken_binary.py tests/regress_reject_invalid_ticket.py tests/regress_reoffer_infra_retry.py tests/regress_requisition_events_owner_stem.py tests/regress_requisition_park_not_attempt.py tests/regress_requisition_prior_review.py tests/regress_requisition_stage_events.py tests/regress_retro_reemit_skip.py tests/regress_review_intakes_own_stem.py tests/regress_review_menu_committed_unlocked.py tests/regress_serve_reoffer_dispatch.py tests/regress_serve_reoffer_rule.py tests/regress_shared_hold_rule.py tests/regress_snapshot_latency.py tests/regress_snapshot_verdict_menu_parity.py tests/regress_stale_running.py tests/regress_status_optional_locks.py tests/regress_status_retires_settled_rows.py tests/regress_step_kind_icons.py tests/regress_suggest_lands_in_box.py tests/regress_triage_author_invoked_boundary.py tests/regress_verdict_decisions_retire_on_resolution.py tests/regress_verdict_submitted_message.py tests/regress_vscode_task_identity.py tests/regress_watch_surface_tier_truth.py tests/regress_watch_tests_fixture_repo.py tests/snapshot_scale_fixture.py tests/waiting.py
./dev.py test
```

## Definition of rejected
- A block key beyond `schema` plus the six listed keys, or a file edited outside its block.
- A `purpose` copied from a different file, left empty, or written by hand per file with different rules from the rule above.
- A change to `pyproject.toml`, `config.yaml` or any ruff exemption.
- More than 1499 inserted lines.

## Time budget
- expected: 25m
- stuck: 50m
- reason: one mechanical refresh plus a purpose pass over about 133 files; they share one command and the Check stage proves them together, so they cannot merge separately.
