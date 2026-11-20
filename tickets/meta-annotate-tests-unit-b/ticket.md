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
`meta-schema-and-refresh-r2` ships `clutch meta refresh` and `clutch meta check` and the `meta.paths` roots in `config.yaml`. After this ticket the 136 tracked `.md` and `.py` files in the second half of `tests/unit/` by file name each carry a valid `clutch.meta/1.0` block, so `uv run clutch meta check` on exactly those files exits 0.

Why: the first attempt at `meta-schema-and-refresh-r2` annotated about 600 files in one diff of 5512 inserted lines and failed the 1500-line diff budget (`diagnosis.json`, verdict split). This ticket is one shard of that work, sized under the budget at about 9 inserted lines per file, so it can merge.

## Boundary contract
none
- reason: metadata only; each file gains a comment block that no code or test reads, produced by the unchanged `clutch meta refresh`, and no behavior, parser or consumer changes

## Scope in / Scope out
In: Block placement is verified against the format gate. `ruff format` requires a blank line between a module docstring and the next code, and the original blank line stays there: refresh inserts the block right after the docstring, so the file reads docstring, `# clutch:meta` block, the original blank line, then code. Checked 2026-11-20 with ruff 0.17.3: `ruff format --diff` on exactly that shape (a docstring line, the eight block lines, one blank line, `import os`) reports `1 file already formatted`, and ruff reformats only the shape with no blank line after the comment (docstring, comment, `import os`), which a tracked file cannot have because it is already `ruff format`-clean. So `parse` still finds the block at the offset after the docstring, and `clutch/meta.py` needs no change. The same check on the real file `tests/integration/test_ladder.py` (block inserted by `meta.refresh`'s own offset and renderer into a temporary copy) reported `1 file already formatted` and `meta.parse` found the block. Black's lone-docstring rule is not what governs this file, since ruff counted the comment block plus the following blank line as the separation. `uv run ruff format --check` over the shard's `.py` files is part of `## Verification` so this holds for every file. Then run `uv run clutch meta refresh` on exactly the files listed in `## Scope fence`, then give each block a non-empty `purpose`, because refresh inserts it empty and `meta check` reports `empty_purpose` for that. `meta fill` does not exist and is out of scope, so purposes are set with a throwaway script that is not committed and not fenced. Purpose rule, applied to every file the same way: for a `.py` file, the first line of its module docstring, else the file stem with `_` and `-` replaced by spaces; for a `.md` file, the text of its first `#` heading, else the file stem with `-` replaced by spaces; cut to at most 120 characters and never empty. Do not edit `relates`, `owner`, `kind`, `verified` or `hash` by hand. Refresh keeps every generated `# relates:` line within the line length that `meta-schema-and-refresh-r2` fixes, so no lint exemption is added and `pyproject.toml` is not touched. A file that fails `ruff` or an existing test only because of its new block is fixed in the block, never by editing the file's body.

Out: every other file, `clutch/specs/`, `meta fill`, the `meta_drift` gate, Check-time refresh, and any change to `config.yaml` (the roots are set by `meta-schema-and-refresh-r2`).

## Scope fence
- tests/unit/test_main_view_events.py
- tests/unit/test_main_view_group.py
- tests/unit/test_menu_admission.py
- tests/unit/test_merge_admission_params.py
- tests/unit/test_merge_dirty.py
- tests/unit/test_merge_resolve.py
- tests/unit/test_mergequeue_offer_ctx.py
- tests/unit/test_mergequeue_retained_ticket.py
- tests/unit/test_meta_block.py
- tests/unit/test_meta_cli.py
- tests/unit/test_meta_config.py
- tests/unit/test_meta_refresh.py
- tests/unit/test_new_evidence.py
- tests/unit/test_observe_extension_fields.py
- tests/unit/test_observe_hot_paths.py
- tests/unit/test_observe_journal_facts.py
- tests/unit/test_panel_combiners.py
- tests/unit/test_panel_member_keys.py
- tests/unit/test_parallel_config.py
- tests/unit/test_parse_ticket_evidence.py
- tests/unit/test_paved_roads.py
- tests/unit/test_phase_events.py
- tests/unit/test_preflight_latest_lookup.py
- tests/unit/test_preflight_parallel.py
- tests/unit/test_premise_overruled.py
- tests/unit/test_premise_park_keep.py
- tests/unit/test_probe_verb.py
- tests/unit/test_projection_helpers_single_owner.py
- tests/unit/test_projection_leftovers.py
- tests/unit/test_provider_parsed_events.py
- tests/unit/test_qwen_adapter.py
- tests/unit/test_readme.py
- tests/unit/test_reject_reason_paths.py
- tests/unit/test_release.py
- tests/unit/test_release_changelog.py
- tests/unit/test_release_packages.py
- tests/unit/test_release_publish.py
- tests/unit/test_requisition_dependents.py
- tests/unit/test_requisition_prior_review.py
- tests/unit/test_requisition_sibling_tickets.py
- tests/unit/test_requisition_stage_events.py
- tests/unit/test_retro_check_vocabulary.py
- tests/unit/test_retro_conflict_paths.py
- tests/unit/test_retro_measurements.py
- tests/unit/test_retro_proposal.py
- tests/unit/test_retro_recurrence.py
- tests/unit/test_retro_settled_trigger.py
- tests/unit/test_rework_review_prior.py
- tests/unit/test_rework_supervise_gate.py
- tests/unit/test_roadmap_accept.py
- tests/unit/test_roadmap_author.py
- tests/unit/test_roadmap_drive.py
- tests/unit/test_roadmap_fresh_write.py
- tests/unit/test_roadmap_gate.py
- tests/unit/test_roadmap_merged.py
- tests/unit/test_roadmap_merged_parallel.py
- tests/unit/test_roadmap_named_stem.py
- tests/unit/test_roadmap_operator_reject_reason.py
- tests/unit/test_roadmap_refile.py
- tests/unit/test_roadmap_refile_ready.py
- tests/unit/test_roadmap_rejection_reason.py
- tests/unit/test_roadmap_rejection_reason_rework_findings.py
- tests/unit/test_roadmap_release_audit_order.py
- tests/unit/test_roadmap_release_boundary.py
- tests/unit/test_roadmap_ship.py
- tests/unit/test_roadmap_start_gates.py
- tests/unit/test_roadmap_status.py
- tests/unit/test_roadmap_stuck_rows.py
- tests/unit/test_roadmap_table.py
- tests/unit/test_route_kinds_filter.py
- tests/unit/test_route_kinds_judge.py
- tests/unit/test_route_panel_config.py
- tests/unit/test_run_stages_propagates.py
- tests/unit/test_runner_attempt_manifest.py
- tests/unit/test_runner_dead_dependents.py
- tests/unit/test_runner_mark_running.py
- tests/unit/test_runner_prepared_dispatch.py
- tests/unit/test_runner_rework_findings_terminal.py
- tests/unit/test_runner_terminal_removal_shield.py
- tests/unit/test_scaffold.py
- tests/unit/test_scheduler_parallel_fill.py
- tests/unit/test_scheduler_returns_on_slot.py
- tests/unit/test_scheduler_write_queue_seams.py
- tests/unit/test_seam_replace.py
- tests/unit/test_seams_rusage.py
- tests/unit/test_seams_unwind_capture.py
- tests/unit/test_serve_driver_overlap.py
- tests/unit/test_serve_responsiveness.py
- tests/unit/test_serve_scheduler_lifecycle.py
- tests/unit/test_shared_fakes.py
- tests/unit/test_snapshot_merged_cap.py
- tests/unit/test_specs.py
- tests/unit/test_specs_json_reply_rule.py
- tests/unit/test_stage_events_seam.py
- tests/unit/test_stages_base_red.py
- tests/unit/test_stages_candidates_select.py
- tests/unit/test_stages_conflict_rerun_inputs.py
- tests/unit/test_stages_flake_coverage.py
- tests/unit/test_stages_host_lock.py
- tests/unit/test_stages_host_path.py
- tests/unit/test_stages_render_check.py
- tests/unit/test_stale_running.py
- tests/unit/test_stats.py
- tests/unit/test_status_retirement.py
- tests/unit/test_status_verdict_decisions.py
- tests/unit/test_step_names_cover_surfaces.py
- tests/unit/test_storm_producer_builder.py
- tests/unit/test_suggest_box.py
- tests/unit/test_supervise_cap_lineage.py
- tests/unit/test_supervise_idle_hooks.py
- tests/unit/test_supervise_idle_point.py
- tests/unit/test_supervise_merge_route.py
- tests/unit/test_supervisor_trigger.py
- tests/unit/test_testreport_reader.py
- tests/unit/test_ticket_budget_limits.py
- tests/unit/test_ticket_lint_rules.py
- tests/unit/test_tickets_context.py
- tests/unit/test_tickets_tolerant_reader.py
- tests/unit/test_training_config.py
- tests/unit/test_training_eval.py
- tests/unit/test_training_export.py
- tests/unit/test_training_export_conflict.py
- tests/unit/test_training_export_kinds.py
- tests/unit/test_training_ticket_kind.py
- tests/unit/test_training_trajectory.py
- tests/unit/test_triage_author_boundary.py
- tests/unit/test_triage_tombstone_rejected.py
- tests/unit/test_update_config_verb.py
- tests/unit/test_verdict_extension.py
- tests/unit/test_verdict_menu_parity.py
- tests/unit/test_verdict_submitted_message.py
- tests/unit/test_view_events.py
- tests/unit/test_visual_baseline.py
- tests/unit/test_visual_review.py
- tests/unit/test_visual_select.py
- tests/unit/test_watchdog_gemini.py

## Acceptance criteria
1. Each of the 136 files in `## Scope fence` starts a valid block with a matching hash and a non-empty `purpose`, so `uv run clutch meta check` on those files exits 0 with no `missing`, `empty_purpose`, `drifted` or `malformed` finding, not just a pass because it was given an empty list. Check: `uv run clutch meta check` over the same paths as `## Verification`.
2. The diff inserts fewer than 1500 lines and deletes none, and each changed file differs from its base only by its block. Check: `./dev.py test` in `## Verification` and the Check stage's `diff_budget` gate.
3. No file outside `## Scope fence` changes, and no `.md` file with frontmatter loses `---` at byte 0. Check: `./dev.py test` in `## Verification`.

## Verification
```
uv run clutch meta check tests/unit/test_main_view_events.py tests/unit/test_main_view_group.py tests/unit/test_menu_admission.py tests/unit/test_merge_admission_params.py tests/unit/test_merge_dirty.py tests/unit/test_merge_resolve.py tests/unit/test_mergequeue_offer_ctx.py tests/unit/test_mergequeue_retained_ticket.py tests/unit/test_meta_block.py tests/unit/test_meta_cli.py tests/unit/test_meta_config.py tests/unit/test_meta_refresh.py tests/unit/test_new_evidence.py tests/unit/test_observe_extension_fields.py tests/unit/test_observe_hot_paths.py tests/unit/test_observe_journal_facts.py tests/unit/test_panel_combiners.py tests/unit/test_panel_member_keys.py tests/unit/test_parallel_config.py tests/unit/test_parse_ticket_evidence.py tests/unit/test_paved_roads.py tests/unit/test_phase_events.py tests/unit/test_preflight_latest_lookup.py tests/unit/test_preflight_parallel.py tests/unit/test_premise_overruled.py tests/unit/test_premise_park_keep.py tests/unit/test_probe_verb.py tests/unit/test_projection_helpers_single_owner.py tests/unit/test_projection_leftovers.py tests/unit/test_provider_parsed_events.py tests/unit/test_qwen_adapter.py tests/unit/test_readme.py tests/unit/test_reject_reason_paths.py tests/unit/test_release.py tests/unit/test_release_changelog.py tests/unit/test_release_packages.py tests/unit/test_release_publish.py tests/unit/test_requisition_dependents.py tests/unit/test_requisition_prior_review.py tests/unit/test_requisition_sibling_tickets.py tests/unit/test_requisition_stage_events.py tests/unit/test_retro_check_vocabulary.py tests/unit/test_retro_conflict_paths.py tests/unit/test_retro_measurements.py tests/unit/test_retro_proposal.py tests/unit/test_retro_recurrence.py tests/unit/test_retro_settled_trigger.py tests/unit/test_rework_review_prior.py tests/unit/test_rework_supervise_gate.py tests/unit/test_roadmap_accept.py tests/unit/test_roadmap_author.py tests/unit/test_roadmap_drive.py tests/unit/test_roadmap_fresh_write.py tests/unit/test_roadmap_gate.py tests/unit/test_roadmap_merged.py tests/unit/test_roadmap_merged_parallel.py tests/unit/test_roadmap_named_stem.py tests/unit/test_roadmap_operator_reject_reason.py tests/unit/test_roadmap_refile.py tests/unit/test_roadmap_refile_ready.py tests/unit/test_roadmap_rejection_reason.py tests/unit/test_roadmap_rejection_reason_rework_findings.py tests/unit/test_roadmap_release_audit_order.py tests/unit/test_roadmap_release_boundary.py tests/unit/test_roadmap_ship.py tests/unit/test_roadmap_start_gates.py tests/unit/test_roadmap_status.py tests/unit/test_roadmap_stuck_rows.py tests/unit/test_roadmap_table.py tests/unit/test_route_kinds_filter.py tests/unit/test_route_kinds_judge.py tests/unit/test_route_panel_config.py tests/unit/test_run_stages_propagates.py tests/unit/test_runner_attempt_manifest.py tests/unit/test_runner_dead_dependents.py tests/unit/test_runner_mark_running.py tests/unit/test_runner_prepared_dispatch.py tests/unit/test_runner_rework_findings_terminal.py tests/unit/test_runner_terminal_removal_shield.py tests/unit/test_scaffold.py tests/unit/test_scheduler_parallel_fill.py tests/unit/test_scheduler_returns_on_slot.py tests/unit/test_scheduler_write_queue_seams.py tests/unit/test_seam_replace.py tests/unit/test_seams_rusage.py tests/unit/test_seams_unwind_capture.py tests/unit/test_serve_driver_overlap.py tests/unit/test_serve_responsiveness.py tests/unit/test_serve_scheduler_lifecycle.py tests/unit/test_shared_fakes.py tests/unit/test_snapshot_merged_cap.py tests/unit/test_specs.py tests/unit/test_specs_json_reply_rule.py tests/unit/test_stage_events_seam.py tests/unit/test_stages_base_red.py tests/unit/test_stages_candidates_select.py tests/unit/test_stages_conflict_rerun_inputs.py tests/unit/test_stages_flake_coverage.py tests/unit/test_stages_host_lock.py tests/unit/test_stages_host_path.py tests/unit/test_stages_render_check.py tests/unit/test_stale_running.py tests/unit/test_stats.py tests/unit/test_status_retirement.py tests/unit/test_status_verdict_decisions.py tests/unit/test_step_names_cover_surfaces.py tests/unit/test_storm_producer_builder.py tests/unit/test_suggest_box.py tests/unit/test_supervise_cap_lineage.py tests/unit/test_supervise_idle_hooks.py tests/unit/test_supervise_idle_point.py tests/unit/test_supervise_merge_route.py tests/unit/test_supervisor_trigger.py tests/unit/test_testreport_reader.py tests/unit/test_ticket_budget_limits.py tests/unit/test_ticket_lint_rules.py tests/unit/test_tickets_context.py tests/unit/test_tickets_tolerant_reader.py tests/unit/test_training_config.py tests/unit/test_training_eval.py tests/unit/test_training_export.py tests/unit/test_training_export_conflict.py tests/unit/test_training_export_kinds.py tests/unit/test_training_ticket_kind.py tests/unit/test_training_trajectory.py tests/unit/test_triage_author_boundary.py tests/unit/test_triage_tombstone_rejected.py tests/unit/test_update_config_verb.py tests/unit/test_verdict_extension.py tests/unit/test_verdict_menu_parity.py tests/unit/test_verdict_submitted_message.py tests/unit/test_view_events.py tests/unit/test_visual_baseline.py tests/unit/test_visual_review.py tests/unit/test_visual_select.py tests/unit/test_watchdog_gemini.py
uv run ruff format --check tests/unit/test_main_view_events.py tests/unit/test_main_view_group.py tests/unit/test_menu_admission.py tests/unit/test_merge_admission_params.py tests/unit/test_merge_dirty.py tests/unit/test_merge_resolve.py tests/unit/test_mergequeue_offer_ctx.py tests/unit/test_mergequeue_retained_ticket.py tests/unit/test_meta_block.py tests/unit/test_meta_cli.py tests/unit/test_meta_config.py tests/unit/test_meta_refresh.py tests/unit/test_new_evidence.py tests/unit/test_observe_extension_fields.py tests/unit/test_observe_hot_paths.py tests/unit/test_observe_journal_facts.py tests/unit/test_panel_combiners.py tests/unit/test_panel_member_keys.py tests/unit/test_parallel_config.py tests/unit/test_parse_ticket_evidence.py tests/unit/test_paved_roads.py tests/unit/test_phase_events.py tests/unit/test_preflight_latest_lookup.py tests/unit/test_preflight_parallel.py tests/unit/test_premise_overruled.py tests/unit/test_premise_park_keep.py tests/unit/test_probe_verb.py tests/unit/test_projection_helpers_single_owner.py tests/unit/test_projection_leftovers.py tests/unit/test_provider_parsed_events.py tests/unit/test_qwen_adapter.py tests/unit/test_readme.py tests/unit/test_reject_reason_paths.py tests/unit/test_release.py tests/unit/test_release_changelog.py tests/unit/test_release_packages.py tests/unit/test_release_publish.py tests/unit/test_requisition_dependents.py tests/unit/test_requisition_prior_review.py tests/unit/test_requisition_sibling_tickets.py tests/unit/test_requisition_stage_events.py tests/unit/test_retro_check_vocabulary.py tests/unit/test_retro_conflict_paths.py tests/unit/test_retro_measurements.py tests/unit/test_retro_proposal.py tests/unit/test_retro_recurrence.py tests/unit/test_retro_settled_trigger.py tests/unit/test_rework_review_prior.py tests/unit/test_rework_supervise_gate.py tests/unit/test_roadmap_accept.py tests/unit/test_roadmap_author.py tests/unit/test_roadmap_drive.py tests/unit/test_roadmap_fresh_write.py tests/unit/test_roadmap_gate.py tests/unit/test_roadmap_merged.py tests/unit/test_roadmap_merged_parallel.py tests/unit/test_roadmap_named_stem.py tests/unit/test_roadmap_operator_reject_reason.py tests/unit/test_roadmap_refile.py tests/unit/test_roadmap_refile_ready.py tests/unit/test_roadmap_rejection_reason.py tests/unit/test_roadmap_rejection_reason_rework_findings.py tests/unit/test_roadmap_release_audit_order.py tests/unit/test_roadmap_release_boundary.py tests/unit/test_roadmap_ship.py tests/unit/test_roadmap_start_gates.py tests/unit/test_roadmap_status.py tests/unit/test_roadmap_stuck_rows.py tests/unit/test_roadmap_table.py tests/unit/test_route_kinds_filter.py tests/unit/test_route_kinds_judge.py tests/unit/test_route_panel_config.py tests/unit/test_run_stages_propagates.py tests/unit/test_runner_attempt_manifest.py tests/unit/test_runner_dead_dependents.py tests/unit/test_runner_mark_running.py tests/unit/test_runner_prepared_dispatch.py tests/unit/test_runner_rework_findings_terminal.py tests/unit/test_runner_terminal_removal_shield.py tests/unit/test_scaffold.py tests/unit/test_scheduler_parallel_fill.py tests/unit/test_scheduler_returns_on_slot.py tests/unit/test_scheduler_write_queue_seams.py tests/unit/test_seam_replace.py tests/unit/test_seams_rusage.py tests/unit/test_seams_unwind_capture.py tests/unit/test_serve_driver_overlap.py tests/unit/test_serve_responsiveness.py tests/unit/test_serve_scheduler_lifecycle.py tests/unit/test_shared_fakes.py tests/unit/test_snapshot_merged_cap.py tests/unit/test_specs.py tests/unit/test_specs_json_reply_rule.py tests/unit/test_stage_events_seam.py tests/unit/test_stages_base_red.py tests/unit/test_stages_candidates_select.py tests/unit/test_stages_conflict_rerun_inputs.py tests/unit/test_stages_flake_coverage.py tests/unit/test_stages_host_lock.py tests/unit/test_stages_host_path.py tests/unit/test_stages_render_check.py tests/unit/test_stale_running.py tests/unit/test_stats.py tests/unit/test_status_retirement.py tests/unit/test_status_verdict_decisions.py tests/unit/test_step_names_cover_surfaces.py tests/unit/test_storm_producer_builder.py tests/unit/test_suggest_box.py tests/unit/test_supervise_cap_lineage.py tests/unit/test_supervise_idle_hooks.py tests/unit/test_supervise_idle_point.py tests/unit/test_supervise_merge_route.py tests/unit/test_supervisor_trigger.py tests/unit/test_testreport_reader.py tests/unit/test_ticket_budget_limits.py tests/unit/test_ticket_lint_rules.py tests/unit/test_tickets_context.py tests/unit/test_tickets_tolerant_reader.py tests/unit/test_training_config.py tests/unit/test_training_eval.py tests/unit/test_training_export.py tests/unit/test_training_export_conflict.py tests/unit/test_training_export_kinds.py tests/unit/test_training_ticket_kind.py tests/unit/test_training_trajectory.py tests/unit/test_triage_author_boundary.py tests/unit/test_triage_tombstone_rejected.py tests/unit/test_update_config_verb.py tests/unit/test_verdict_extension.py tests/unit/test_verdict_menu_parity.py tests/unit/test_verdict_submitted_message.py tests/unit/test_view_events.py tests/unit/test_visual_baseline.py tests/unit/test_visual_review.py tests/unit/test_visual_select.py tests/unit/test_watchdog_gemini.py
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
- reason: one mechanical refresh plus a purpose pass over about 136 files; they share one command and the Check stage proves them together, so they cannot merge separately.
