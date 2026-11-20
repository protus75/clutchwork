---
state: confirmed
source: human
priority: P2
kind: chore
---

## Depends on
- meta-schema-and-refresh-r2

## Context
- docs/annotations-index-plan.md

## Goal / Why
`meta-schema-and-refresh-r2` ships `clutch meta refresh` and `clutch meta check` and the `meta.paths` roots in `config.yaml`. After this ticket the 133 tracked `.md` and `.py` files in the first half of `tests/unit/` by file name each carry a valid `clutch.meta/1.0` block, so `uv run clutch meta check` on exactly those files exits 0.

Why: the first attempt at `meta-schema-and-refresh-r2` annotated about 600 files in one diff of 5512 inserted lines and failed the 1500-line diff budget (`diagnosis.json`, verdict split). This ticket is one shard of that work, sized under the budget at about 9 inserted lines per file, so it can merge.

## Boundary contract
none
- reason: metadata only; each file gains a comment block that no code or test reads, produced by the unchanged `clutch meta refresh`, and no behavior, parser or consumer changes

## Scope in / Scope out
In: Block placement is verified against the format gate. `ruff format` requires a blank line between a module docstring and the next code, and the original blank line stays there: refresh inserts the block right after the docstring, so the file reads docstring, `# clutch:meta` block, the original blank line, then code. Checked 2026-11-20 with ruff 0.17.3: `ruff format --diff` on exactly that shape (a docstring line, the eight block lines, one blank line, `import os`) reports `1 file already formatted`, and ruff reformats only the shape with no blank line after the comment (docstring, comment, `import os`), which a tracked file cannot have because it is already `ruff format`-clean. So `parse` still finds the block at the offset after the docstring, and `clutch/meta.py` needs no change. `uv run ruff format --check` over the shard's `.py` files is part of `## Verification` so this holds for every file. Then run `uv run clutch meta refresh` on exactly the files listed in `## Scope fence`, then give each block a non-empty `purpose`, because refresh inserts it empty and `meta check` reports `empty_purpose` for that. `meta fill` does not exist and is out of scope, so purposes are set with a throwaway script that is not committed and not fenced. Purpose rule, applied to every file the same way: for a `.py` file, the first line of its module docstring, else the file stem with `_` and `-` replaced by spaces; for a `.md` file, the text of its first `#` heading, else the file stem with `-` replaced by spaces; cut to at most 120 characters and never empty. Do not edit `relates`, `owner`, `kind`, `verified` or `hash` by hand. Refresh keeps every generated `# relates:` line within the line length that `meta-schema-and-refresh-r2` fixes, so no lint exemption is added and `pyproject.toml` is not touched. A file that fails `ruff` or an existing test only because of its new block is fixed in the block, never by editing the file's body.

Out: every other file, `clutch/specs/`, `meta fill`, the `meta_drift` gate, Check-time refresh, and any change to `config.yaml` (the roots are set by `meta-schema-and-refresh-r2`).

## Scope fence
- tests/unit/__init__.py
- tests/unit/test_admission_facts.py
- tests/unit/test_admission_parallel_run_set.py
- tests/unit/test_admission_running_set.py
- tests/unit/test_artifacts.py
- tests/unit/test_artifacts_harvest_cost_source.py
- tests/unit/test_artifacts_refused.py
- tests/unit/test_ask_drafts.py
- tests/unit/test_ask_drain_loop.py
- tests/unit/test_ask_plan_drain.py
- tests/unit/test_ask_plan_serve.py
- tests/unit/test_ask_roadmap.py
- tests/unit/test_author.py
- tests/unit/test_author_calibration.py
- tests/unit/test_author_decline_findings.py
- tests/unit/test_author_roadmap_row.py
- tests/unit/test_author_scope_out_deferral.py
- tests/unit/test_author_slice_follow_up.py
- tests/unit/test_author_stem_claimed.py
- tests/unit/test_author_ticket_state.py
- tests/unit/test_baseline_visual.py
- tests/unit/test_boundary_contract_required.py
- tests/unit/test_boundary_contract_shape.py
- tests/unit/test_calibration.py
- tests/unit/test_calibration_idle.py
- tests/unit/test_callerless_code_removed.py
- tests/unit/test_callmeter_events.py
- tests/unit/test_caps_conflict_rerun.py
- tests/unit/test_caps_requisition_park.py
- tests/unit/test_chain_order.py
- tests/unit/test_changelog.py
- tests/unit/test_check_timing.py
- tests/unit/test_checkpoint_settled_count.py
- tests/unit/test_closed_sets_remaining.py
- tests/unit/test_closed_sets_single_owner.py
- tests/unit/test_codex_effort.py
- tests/unit/test_commit_lock.py
- tests/unit/test_conflict_rerun_runs_alone.py
- tests/unit/test_conflict_rerun_swap.py
- tests/unit/test_control_known.py
- tests/unit/test_control_operator_reason.py
- tests/unit/test_control_triage_request.py
- tests/unit/test_covgate.py
- tests/unit/test_daemon_admission_busy.py
- tests/unit/test_dev_testguard.py
- tests/unit/test_diagnosis_lesson_trim.py
- tests/unit/test_dispatch_settle.py
- tests/unit/test_docs_verb.py
- tests/unit/test_drain_containment.py
- tests/unit/test_drain_deadline.py
- tests/unit/test_drain_detach_cli.py
- tests/unit/test_drain_driver_overlap.py
- tests/unit/test_drain_eligible.py
- tests/unit/test_drain_reoffer.py
- tests/unit/test_drain_report_intake.py
- tests/unit/test_drain_serve_triage_idle.py
- tests/unit/test_driver_check_nesting.py
- tests/unit/test_driver_from_config_journal.py
- tests/unit/test_driver_hooks.py
- tests/unit/test_driver_panel_fanout.py
- tests/unit/test_driver_unwrap_prose.py
- tests/unit/test_effects_recorded.py
- tests/unit/test_engine_signals.py
- tests/unit/test_evidence_attempt_manifest.py
- tests/unit/test_evidence_attempts_listing.py
- tests/unit/test_evidence_claude.py
- tests/unit/test_evidence_codex.py
- tests/unit/test_evidence_config.py
- tests/unit/test_evidence_envelope.py
- tests/unit/test_evidence_gemini.py
- tests/unit/test_evidence_rusage_record.py
- tests/unit/test_evidence_schema.py
- tests/unit/test_evidence_scoped_key.py
- tests/unit/test_evidence_store.py
- tests/unit/test_fence_overlap.py
- tests/unit/test_fs_seam_mkdir_remove.py
- tests/unit/test_fs_seam_read_size.py
- tests/unit/test_gemini_adapter.py
- tests/unit/test_git_commit.py
- tests/unit/test_git_main_write.py
- tests/unit/test_git_merged_tickets_parse.py
- tests/unit/test_git_tree_id.py
- tests/unit/test_go_panel_schema.py
- tests/unit/test_graph.py
- tests/unit/test_graphics_kind.py
- tests/unit/test_graphics_new.py
- tests/unit/test_graphics_presence_grammar.py
- tests/unit/test_harvest_redaction.py
- tests/unit/test_help.py
- tests/unit/test_help_snapshot.py
- tests/unit/test_host_authoring.py
- tests/unit/test_host_check_selection.py
- tests/unit/test_host_running.py
- tests/unit/test_hostfiles.py
- tests/unit/test_hostfiles_duckdb_rule.py
- tests/unit/test_hostfiles_supervisor_verdicts.py
- tests/unit/test_images_checks.py
- tests/unit/test_images_embedding.py
- tests/unit/test_images_gate.py
- tests/unit/test_images_scores.py
- tests/unit/test_implement_incomplete.py
- tests/unit/test_implement_premise_path.py
- tests/unit/test_init_config_verb.py
- tests/unit/test_install_verb.py
- tests/unit/test_intake_plan.py
- tests/unit/test_intake_scope.py
- tests/unit/test_issue_link.py
- tests/unit/test_issue_process_gap.py
- tests/unit/test_journal_duckdb_cache.py
- tests/unit/test_journal_incremental.py
- tests/unit/test_journal_last_transition.py
- tests/unit/test_journal_ts_under_lock.py
- tests/unit/test_key_scope.py
- tests/unit/test_lift_decision.py
- tests/unit/test_lint_ceiling.py
- tests/unit/test_lint_guide_parity.py
- tests/unit/test_live_call.py
- tests/unit/test_lock_holder.py
- tests/unit/test_main_box_group.py
- tests/unit/test_main_config_group.py
- tests/unit/test_main_coverage_group.py
- tests/unit/test_main_engine_calibrate.py
- tests/unit/test_main_engine_control.py
- tests/unit/test_main_engine_group.py
- tests/unit/test_main_help.py
- tests/unit/test_main_host_group.py
- tests/unit/test_main_meta_group.py
- tests/unit/test_main_provider_group.py
- tests/unit/test_main_release_group.py
- tests/unit/test_main_ticket_group.py
- tests/unit/test_main_ticket_verdicts.py
- tests/unit/test_main_training_group.py
- tests/unit/test_main_verb_groups.py

## Acceptance criteria
1. Each of the 133 files in `## Scope fence` starts a valid block with a matching hash and a non-empty `purpose`, so `uv run clutch meta check` on those files exits 0 with no `missing`, `empty_purpose`, `drifted` or `malformed` finding, not just a pass because it was given an empty list. Check: `uv run clutch meta check` over the same paths as `## Verification`.
2. The diff inserts fewer than 1500 lines and deletes none, and each changed file differs from its base only by its block. Check: `./dev.py test` in `## Verification` and the Check stage's `diff_budget` gate.
3. No file outside `## Scope fence` changes, and no `.md` file with frontmatter loses `---` at byte 0. Check: `./dev.py test` in `## Verification`.

## Verification
```
uv run clutch meta check tests/unit/__init__.py tests/unit/test_admission_facts.py tests/unit/test_admission_parallel_run_set.py tests/unit/test_admission_running_set.py tests/unit/test_artifacts.py tests/unit/test_artifacts_harvest_cost_source.py tests/unit/test_artifacts_refused.py tests/unit/test_ask_drafts.py tests/unit/test_ask_drain_loop.py tests/unit/test_ask_plan_drain.py tests/unit/test_ask_plan_serve.py tests/unit/test_ask_roadmap.py tests/unit/test_author.py tests/unit/test_author_calibration.py tests/unit/test_author_decline_findings.py tests/unit/test_author_roadmap_row.py tests/unit/test_author_scope_out_deferral.py tests/unit/test_author_slice_follow_up.py tests/unit/test_author_stem_claimed.py tests/unit/test_author_ticket_state.py tests/unit/test_baseline_visual.py tests/unit/test_boundary_contract_required.py tests/unit/test_boundary_contract_shape.py tests/unit/test_calibration.py tests/unit/test_calibration_idle.py tests/unit/test_callerless_code_removed.py tests/unit/test_callmeter_events.py tests/unit/test_caps_conflict_rerun.py tests/unit/test_caps_requisition_park.py tests/unit/test_chain_order.py tests/unit/test_changelog.py tests/unit/test_check_timing.py tests/unit/test_checkpoint_settled_count.py tests/unit/test_closed_sets_remaining.py tests/unit/test_closed_sets_single_owner.py tests/unit/test_codex_effort.py tests/unit/test_commit_lock.py tests/unit/test_conflict_rerun_runs_alone.py tests/unit/test_conflict_rerun_swap.py tests/unit/test_control_known.py tests/unit/test_control_operator_reason.py tests/unit/test_control_triage_request.py tests/unit/test_covgate.py tests/unit/test_daemon_admission_busy.py tests/unit/test_dev_testguard.py tests/unit/test_diagnosis_lesson_trim.py tests/unit/test_dispatch_settle.py tests/unit/test_docs_verb.py tests/unit/test_drain_containment.py tests/unit/test_drain_deadline.py tests/unit/test_drain_detach_cli.py tests/unit/test_drain_driver_overlap.py tests/unit/test_drain_eligible.py tests/unit/test_drain_reoffer.py tests/unit/test_drain_report_intake.py tests/unit/test_drain_serve_triage_idle.py tests/unit/test_driver_check_nesting.py tests/unit/test_driver_from_config_journal.py tests/unit/test_driver_hooks.py tests/unit/test_driver_panel_fanout.py tests/unit/test_driver_unwrap_prose.py tests/unit/test_effects_recorded.py tests/unit/test_engine_signals.py tests/unit/test_evidence_attempt_manifest.py tests/unit/test_evidence_attempts_listing.py tests/unit/test_evidence_claude.py tests/unit/test_evidence_codex.py tests/unit/test_evidence_config.py tests/unit/test_evidence_envelope.py tests/unit/test_evidence_gemini.py tests/unit/test_evidence_rusage_record.py tests/unit/test_evidence_schema.py tests/unit/test_evidence_scoped_key.py tests/unit/test_evidence_store.py tests/unit/test_fence_overlap.py tests/unit/test_fs_seam_mkdir_remove.py tests/unit/test_fs_seam_read_size.py tests/unit/test_gemini_adapter.py tests/unit/test_git_commit.py tests/unit/test_git_main_write.py tests/unit/test_git_merged_tickets_parse.py tests/unit/test_git_tree_id.py tests/unit/test_go_panel_schema.py tests/unit/test_graph.py tests/unit/test_graphics_kind.py tests/unit/test_graphics_new.py tests/unit/test_graphics_presence_grammar.py tests/unit/test_harvest_redaction.py tests/unit/test_help.py tests/unit/test_help_snapshot.py tests/unit/test_host_authoring.py tests/unit/test_host_check_selection.py tests/unit/test_host_running.py tests/unit/test_hostfiles.py tests/unit/test_hostfiles_duckdb_rule.py tests/unit/test_hostfiles_supervisor_verdicts.py tests/unit/test_images_checks.py tests/unit/test_images_embedding.py tests/unit/test_images_gate.py tests/unit/test_images_scores.py tests/unit/test_implement_incomplete.py tests/unit/test_implement_premise_path.py tests/unit/test_init_config_verb.py tests/unit/test_install_verb.py tests/unit/test_intake_plan.py tests/unit/test_intake_scope.py tests/unit/test_issue_link.py tests/unit/test_issue_process_gap.py tests/unit/test_journal_duckdb_cache.py tests/unit/test_journal_incremental.py tests/unit/test_journal_last_transition.py tests/unit/test_journal_ts_under_lock.py tests/unit/test_key_scope.py tests/unit/test_lift_decision.py tests/unit/test_lint_ceiling.py tests/unit/test_lint_guide_parity.py tests/unit/test_live_call.py tests/unit/test_lock_holder.py tests/unit/test_main_box_group.py tests/unit/test_main_config_group.py tests/unit/test_main_coverage_group.py tests/unit/test_main_engine_calibrate.py tests/unit/test_main_engine_control.py tests/unit/test_main_engine_group.py tests/unit/test_main_help.py tests/unit/test_main_host_group.py tests/unit/test_main_meta_group.py tests/unit/test_main_provider_group.py tests/unit/test_main_release_group.py tests/unit/test_main_ticket_group.py tests/unit/test_main_ticket_verdicts.py tests/unit/test_main_training_group.py tests/unit/test_main_verb_groups.py
uv run ruff format --check tests/unit/__init__.py tests/unit/test_admission_facts.py tests/unit/test_admission_parallel_run_set.py tests/unit/test_admission_running_set.py tests/unit/test_artifacts.py tests/unit/test_artifacts_harvest_cost_source.py tests/unit/test_artifacts_refused.py tests/unit/test_ask_drafts.py tests/unit/test_ask_drain_loop.py tests/unit/test_ask_plan_drain.py tests/unit/test_ask_plan_serve.py tests/unit/test_ask_roadmap.py tests/unit/test_author.py tests/unit/test_author_calibration.py tests/unit/test_author_decline_findings.py tests/unit/test_author_roadmap_row.py tests/unit/test_author_scope_out_deferral.py tests/unit/test_author_slice_follow_up.py tests/unit/test_author_stem_claimed.py tests/unit/test_author_ticket_state.py tests/unit/test_baseline_visual.py tests/unit/test_boundary_contract_required.py tests/unit/test_boundary_contract_shape.py tests/unit/test_calibration.py tests/unit/test_calibration_idle.py tests/unit/test_callerless_code_removed.py tests/unit/test_callmeter_events.py tests/unit/test_caps_conflict_rerun.py tests/unit/test_caps_requisition_park.py tests/unit/test_chain_order.py tests/unit/test_changelog.py tests/unit/test_check_timing.py tests/unit/test_checkpoint_settled_count.py tests/unit/test_closed_sets_remaining.py tests/unit/test_closed_sets_single_owner.py tests/unit/test_codex_effort.py tests/unit/test_commit_lock.py tests/unit/test_conflict_rerun_runs_alone.py tests/unit/test_conflict_rerun_swap.py tests/unit/test_control_known.py tests/unit/test_control_operator_reason.py tests/unit/test_control_triage_request.py tests/unit/test_covgate.py tests/unit/test_daemon_admission_busy.py tests/unit/test_dev_testguard.py tests/unit/test_diagnosis_lesson_trim.py tests/unit/test_dispatch_settle.py tests/unit/test_docs_verb.py tests/unit/test_drain_containment.py tests/unit/test_drain_deadline.py tests/unit/test_drain_detach_cli.py tests/unit/test_drain_driver_overlap.py tests/unit/test_drain_eligible.py tests/unit/test_drain_reoffer.py tests/unit/test_drain_report_intake.py tests/unit/test_drain_serve_triage_idle.py tests/unit/test_driver_check_nesting.py tests/unit/test_driver_from_config_journal.py tests/unit/test_driver_hooks.py tests/unit/test_driver_panel_fanout.py tests/unit/test_driver_unwrap_prose.py tests/unit/test_effects_recorded.py tests/unit/test_engine_signals.py tests/unit/test_evidence_attempt_manifest.py tests/unit/test_evidence_attempts_listing.py tests/unit/test_evidence_claude.py tests/unit/test_evidence_codex.py tests/unit/test_evidence_config.py tests/unit/test_evidence_envelope.py tests/unit/test_evidence_gemini.py tests/unit/test_evidence_rusage_record.py tests/unit/test_evidence_schema.py tests/unit/test_evidence_scoped_key.py tests/unit/test_evidence_store.py tests/unit/test_fence_overlap.py tests/unit/test_fs_seam_mkdir_remove.py tests/unit/test_fs_seam_read_size.py tests/unit/test_gemini_adapter.py tests/unit/test_git_commit.py tests/unit/test_git_main_write.py tests/unit/test_git_merged_tickets_parse.py tests/unit/test_git_tree_id.py tests/unit/test_go_panel_schema.py tests/unit/test_graph.py tests/unit/test_graphics_kind.py tests/unit/test_graphics_new.py tests/unit/test_graphics_presence_grammar.py tests/unit/test_harvest_redaction.py tests/unit/test_help.py tests/unit/test_help_snapshot.py tests/unit/test_host_authoring.py tests/unit/test_host_check_selection.py tests/unit/test_host_running.py tests/unit/test_hostfiles.py tests/unit/test_hostfiles_duckdb_rule.py tests/unit/test_hostfiles_supervisor_verdicts.py tests/unit/test_images_checks.py tests/unit/test_images_embedding.py tests/unit/test_images_gate.py tests/unit/test_images_scores.py tests/unit/test_implement_incomplete.py tests/unit/test_implement_premise_path.py tests/unit/test_init_config_verb.py tests/unit/test_install_verb.py tests/unit/test_intake_plan.py tests/unit/test_intake_scope.py tests/unit/test_issue_link.py tests/unit/test_issue_process_gap.py tests/unit/test_journal_duckdb_cache.py tests/unit/test_journal_incremental.py tests/unit/test_journal_last_transition.py tests/unit/test_journal_ts_under_lock.py tests/unit/test_key_scope.py tests/unit/test_lift_decision.py tests/unit/test_lint_ceiling.py tests/unit/test_lint_guide_parity.py tests/unit/test_live_call.py tests/unit/test_lock_holder.py tests/unit/test_main_box_group.py tests/unit/test_main_config_group.py tests/unit/test_main_coverage_group.py tests/unit/test_main_engine_calibrate.py tests/unit/test_main_engine_control.py tests/unit/test_main_engine_group.py tests/unit/test_main_help.py tests/unit/test_main_host_group.py tests/unit/test_main_meta_group.py tests/unit/test_main_provider_group.py tests/unit/test_main_release_group.py tests/unit/test_main_ticket_group.py tests/unit/test_main_ticket_verdicts.py tests/unit/test_main_training_group.py tests/unit/test_main_verb_groups.py
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
