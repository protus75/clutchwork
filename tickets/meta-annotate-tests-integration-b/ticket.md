---
state: draft
source: human
priority: P2
kind: chore
---

## Depends on
- meta-schema-and-refresh-r2

## Context
- docs/annotations-index-plan.md

## Goal / Why
`meta-schema-and-refresh-r2` ships `clutch meta refresh` and `clutch meta check` and the `meta.paths` roots in `config.yaml`. After this ticket the 112 tracked `.md` and `.py` files in the second half of `tests/integration/` by file name each carry a valid `clutch.meta/1.0` block, so `uv run clutch meta check` on exactly those files exits 0.

Why: the first attempt at `meta-schema-and-refresh-r2` annotated about 600 files in one diff of 5512 inserted lines and failed the 1500-line diff budget (`diagnosis.json`, verdict split). This ticket is one shard of that work, sized under the budget at about 9 inserted lines per file, so it can merge.

## Boundary contract
none
- reason: metadata only; each file gains a comment block that no code or test reads, produced by the unchanged `clutch meta refresh`, and no behavior, parser or consumer changes

## Scope in / Scope out
In: run `uv run clutch meta refresh` on exactly the files listed in `## Scope fence`, then give each block a non-empty `purpose`, because refresh inserts it empty and `meta check` reports `empty_purpose` for that. `meta fill` does not exist and is out of scope, so purposes are set with a throwaway script that is not committed and not fenced. Purpose rule, applied to every file the same way: for a `.py` file, the first line of its module docstring, else the file stem with `_` and `-` replaced by spaces; for a `.md` file, the text of its first `#` heading, else the file stem with `-` replaced by spaces; cut to at most 120 characters and never empty. Do not edit `relates`, `owner`, `kind`, `verified` or `hash` by hand. Refresh keeps every generated `# relates:` line within the line length that `meta-schema-and-refresh-r2` fixes, so no lint exemption is added and `pyproject.toml` is not touched. A file that fails `ruff` or an existing test only because of its new block is fixed in the block, never by editing the file's body.

Out: every other file, `clutch/specs/`, `meta fill`, the `meta_drift` gate, Check-time refresh, and any change to `config.yaml` (the roots are set by `meta-schema-and-refresh-r2`).

## Scope fence
- tests/integration/test_kill_worker_stop.py
- tests/integration/test_ladder.py
- tests/integration/test_lint_guide_parity.py
- tests/integration/test_lint_verb.py
- tests/integration/test_live_call_source.py
- tests/integration/test_llm_effect.py
- tests/integration/test_lockfile.py
- tests/integration/test_main_verb_groups.py
- tests/integration/test_menu_verb_parity.py
- tests/integration/test_merge.py
- tests/integration/test_merge_admission_owner.py
- tests/integration/test_merge_model_resolve.py
- tests/integration/test_mergequeue.py
- tests/integration/test_notify.py
- tests/integration/test_open_tickets_closed.py
- tests/integration/test_panel_purity.py
- tests/integration/test_paved_roads.py
- tests/integration/test_policy.py
- tests/integration/test_precondition_rules.py
- tests/integration/test_projection_helpers_source.py
- tests/integration/test_provider_capture_overwrite.py
- tests/integration/test_provider_cooldown_failover.py
- tests/integration/test_provider_failure_surface.py
- tests/integration/test_provider_parsed_fixtures.py
- tests/integration/test_providers.py
- tests/integration/test_reconcile.py
- tests/integration/test_regress_scripts_guarded.py
- tests/integration/test_reject_queue.py
- tests/integration/test_reject_reason_both_paths.py
- tests/integration/test_release.py
- tests/integration/test_release_publish.py
- tests/integration/test_reliability_battery.py
- tests/integration/test_repo_config_parallel.py
- tests/integration/test_requisition.py
- tests/integration/test_requisition_gate.py
- tests/integration/test_requisition_review_stand_in_closure.py
- tests/integration/test_requisition_review_whole_value_closure.py
- tests/integration/test_restart_timers.py
- tests/integration/test_retro.py
- tests/integration/test_retro_box.py
- tests/integration/test_retro_conflict_spec.py
- tests/integration/test_review_command.py
- tests/integration/test_review_spec_rma_codes.py
- tests/integration/test_rework.py
- tests/integration/test_rework_failure_terminal_findings.py
- tests/integration/test_rework_supervise.py
- tests/integration/test_roadmap_author.py
- tests/integration/test_roadmap_driver.py
- tests/integration/test_roadmap_gate.py
- tests/integration/test_roadmap_merged.py
- tests/integration/test_roadmap_named_stem.py
- tests/integration/test_roadmap_refile.py
- tests/integration/test_roadmap_row_author.py
- tests/integration/test_roadmap_ship.py
- tests/integration/test_roadmap_start_gates.py
- tests/integration/test_roadmap_status.py
- tests/integration/test_roadmap_table.py
- tests/integration/test_route_kinds_judge_lint.py
- tests/integration/test_scan_owners.py
- tests/integration/test_scheduler.py
- tests/integration/test_scheduler_seam_source.py
- tests/integration/test_scorecard.py
- tests/integration/test_second_problems.py
- tests/integration/test_serve_admission.py
- tests/integration/test_serve_dispatch.py
- tests/integration/test_serve_driver.py
- tests/integration/test_serve_driver_overlap.py
- tests/integration/test_serve_kill.py
- tests/integration/test_serve_lifecycle.py
- tests/integration/test_serve_notify.py
- tests/integration/test_serve_rig_fakes.py
- tests/integration/test_serve_upgrade.py
- tests/integration/test_shakeout.py
- tests/integration/test_shared_fakes_adoption.py
- tests/integration/test_shared_fakes_adoption_b.py
- tests/integration/test_snapshot_cache_facts.py
- tests/integration/test_snapshot_merged_cap.py
- tests/integration/test_spec_sibling_tickets.py
- tests/integration/test_spec_unit_io_seam.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_specs_json_reply_specs.py
- tests/integration/test_stages.py
- tests/integration/test_stale_running.py
- tests/integration/test_stats.py
- tests/integration/test_status.py
- tests/integration/test_step_events.py
- tests/integration/test_step_icons.py
- tests/integration/test_storm.py
- tests/integration/test_storm_hold.py
- tests/integration/test_storm_notification_activation.py
- tests/integration/test_storm_producer.py
- tests/integration/test_supervise_cap_lineage.py
- tests/integration/test_supervisor_rework.py
- tests/integration/test_sweep_slot_handoff.py
- tests/integration/test_terminal.py
- tests/integration/test_testguard.py
- tests/integration/test_testreport.py
- tests/integration/test_thresh.py
- tests/integration/test_tickets.py
- tests/integration/test_tolerant_reader_callers.py
- tests/integration/test_triage.py
- tests/integration/test_unit_io_rule.py
- tests/integration/test_visual_baseline_dev.py
- tests/integration/test_visual_fixtures.py
- tests/integration/test_visual_review_spec.py
- tests/integration/test_vocabularies.py
- tests/integration/test_vscode_command_not_found.py
- tests/integration/test_watch.py
- tests/integration/test_watch_surface_tier.py
- tests/integration/test_watchdog.py
- tests/integration/test_watchdog_activation.py
- tests/integration/watch_fixture_repo.py

## Acceptance criteria
1. Each of the 112 files in `## Scope fence` starts a valid block with a matching hash and a non-empty `purpose`, so `uv run clutch meta check` on those files exits 0 with no `missing`, `empty_purpose`, `drifted` or `malformed` finding, not just a pass because it was given an empty list. Check: `uv run clutch meta check` over the same paths as `## Verification`.
2. The diff inserts fewer than 1500 lines and deletes none, and each changed file differs from its base only by its block. Check: `./dev.py test` in `## Verification` and the Check stage's `diff_budget` gate.
3. No file outside `## Scope fence` changes, and no `.md` file with frontmatter loses `---` at byte 0. Check: `./dev.py test` in `## Verification`.

## Verification
```
uv run clutch meta check tests/integration/test_kill_worker_stop.py tests/integration/test_ladder.py tests/integration/test_lint_guide_parity.py tests/integration/test_lint_verb.py tests/integration/test_live_call_source.py tests/integration/test_llm_effect.py tests/integration/test_lockfile.py tests/integration/test_main_verb_groups.py tests/integration/test_menu_verb_parity.py tests/integration/test_merge.py tests/integration/test_merge_admission_owner.py tests/integration/test_merge_model_resolve.py tests/integration/test_mergequeue.py tests/integration/test_notify.py tests/integration/test_open_tickets_closed.py tests/integration/test_panel_purity.py tests/integration/test_paved_roads.py tests/integration/test_policy.py tests/integration/test_precondition_rules.py tests/integration/test_projection_helpers_source.py tests/integration/test_provider_capture_overwrite.py tests/integration/test_provider_cooldown_failover.py tests/integration/test_provider_failure_surface.py tests/integration/test_provider_parsed_fixtures.py tests/integration/test_providers.py tests/integration/test_reconcile.py tests/integration/test_regress_scripts_guarded.py tests/integration/test_reject_queue.py tests/integration/test_reject_reason_both_paths.py tests/integration/test_release.py tests/integration/test_release_publish.py tests/integration/test_reliability_battery.py tests/integration/test_repo_config_parallel.py tests/integration/test_requisition.py tests/integration/test_requisition_gate.py tests/integration/test_requisition_review_stand_in_closure.py tests/integration/test_requisition_review_whole_value_closure.py tests/integration/test_restart_timers.py tests/integration/test_retro.py tests/integration/test_retro_box.py tests/integration/test_retro_conflict_spec.py tests/integration/test_review_command.py tests/integration/test_review_spec_rma_codes.py tests/integration/test_rework.py tests/integration/test_rework_failure_terminal_findings.py tests/integration/test_rework_supervise.py tests/integration/test_roadmap_author.py tests/integration/test_roadmap_driver.py tests/integration/test_roadmap_gate.py tests/integration/test_roadmap_merged.py tests/integration/test_roadmap_named_stem.py tests/integration/test_roadmap_refile.py tests/integration/test_roadmap_row_author.py tests/integration/test_roadmap_ship.py tests/integration/test_roadmap_start_gates.py tests/integration/test_roadmap_status.py tests/integration/test_roadmap_table.py tests/integration/test_route_kinds_judge_lint.py tests/integration/test_scan_owners.py tests/integration/test_scheduler.py tests/integration/test_scheduler_seam_source.py tests/integration/test_scorecard.py tests/integration/test_second_problems.py tests/integration/test_serve_admission.py tests/integration/test_serve_dispatch.py tests/integration/test_serve_driver.py tests/integration/test_serve_driver_overlap.py tests/integration/test_serve_kill.py tests/integration/test_serve_lifecycle.py tests/integration/test_serve_notify.py tests/integration/test_serve_rig_fakes.py tests/integration/test_serve_upgrade.py tests/integration/test_shakeout.py tests/integration/test_shared_fakes_adoption.py tests/integration/test_shared_fakes_adoption_b.py tests/integration/test_snapshot_cache_facts.py tests/integration/test_snapshot_merged_cap.py tests/integration/test_spec_sibling_tickets.py tests/integration/test_spec_unit_io_seam.py tests/integration/test_specs_delimiter_note.py tests/integration/test_specs_json_reply_specs.py tests/integration/test_stages.py tests/integration/test_stale_running.py tests/integration/test_stats.py tests/integration/test_status.py tests/integration/test_step_events.py tests/integration/test_step_icons.py tests/integration/test_storm.py tests/integration/test_storm_hold.py tests/integration/test_storm_notification_activation.py tests/integration/test_storm_producer.py tests/integration/test_supervise_cap_lineage.py tests/integration/test_supervisor_rework.py tests/integration/test_sweep_slot_handoff.py tests/integration/test_terminal.py tests/integration/test_testguard.py tests/integration/test_testreport.py tests/integration/test_thresh.py tests/integration/test_tickets.py tests/integration/test_tolerant_reader_callers.py tests/integration/test_triage.py tests/integration/test_unit_io_rule.py tests/integration/test_visual_baseline_dev.py tests/integration/test_visual_fixtures.py tests/integration/test_visual_review_spec.py tests/integration/test_vocabularies.py tests/integration/test_vscode_command_not_found.py tests/integration/test_watch.py tests/integration/test_watch_surface_tier.py tests/integration/test_watchdog.py tests/integration/test_watchdog_activation.py tests/integration/watch_fixture_repo.py
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
- reason: one mechanical refresh plus a purpose pass over about 112 files; they share one command and the Check stage proves them together, so they cannot merge separately.
