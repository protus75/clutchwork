# Review: snag

The conftest hook, test rewrite, doc sentence and the 184 pytestmark lines are correct, but 181 of the skipped files also get rewritten clutch:meta purpose, owner or relates lines that the ticket forbids ('Nothing else in those files changes'; Definition of rejected: any other changed line), and meta refresh changes only verified/hash, so none of these edits was forced.

## Findings

- [scope] tests/integration/test_ask.py:4 Rewrites the clutch:meta purpose line in a skipped file; the ticket allows only the pytestmark line and `import pytest` to change. (do instead: Put back the base-commit purpose line; keep only the marker, the import, and the verified/hash refresh.)
- [scope] tests/integration/test_ask_drafts.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_ask_drain_loop.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_ask_drain_loop_agent.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_ask_plan_conduct_covered.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_ask_plan_drain.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_ask_plan_priority_order.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_ask_plan_read_queue.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_ask_plan_serve.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_ask_plan_shared_paths.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_ask_plan_subagent_models.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_ask_roadmap.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_ask_view_events.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_audit.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_author.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_baseline.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_box.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_box_triage_inbox.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_bug_gate.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_caps.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_checkpoint.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_closed_sets.py:11 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_closed_sets_remaining.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_config.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_conflict_rerun_swap.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_context_suggest_cli.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_control.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_control_cli.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_covgate.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_covmap.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_daemon_admission.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_daemon_composition.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_daemon_config.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_daemon_core_queue_seams.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_daemon_pause.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_daemon_soak.py:9 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_daemon_soak_runner.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_daemon_tasks.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_dev.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_dev_vscode_package_kept.py:4 Rewrites the meta purpose line, and changes owner from engine to dev.py on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_diagnose.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_diagnose_eval.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_doctor.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_drain.py:9 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_drain_admissions.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_drain_containment.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_drain_detach.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_drain_reentry.py:10 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_drain_signals.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_drain_upgrade.py:9 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_driver.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_echo_stage.py:6 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_effects.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_eval_harness.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_evidence_captures_verb.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_evidence_envelope.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_evidence_verbs.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_extension_draw_failure.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_fault_injection.py:12 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_fixture_host.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_flake.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_gates.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_gemini_provider.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_go_ai_panel.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_go_grade.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_handoff_replace.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_harvest.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_harvest_cost_source.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_harvest_orphans.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_heartbeat.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_host_contract.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_host_loop.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_host_mechanical.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_hostfiles.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_hot_paths_snapshot.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_image_candidates_select.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_implement_related_files_prompt.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_inbox.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_index_cli.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_index_extensions.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_index_neighbors_fulltext.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_intake_keeps_draft.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_intake_scope.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_issue_verb.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_kill_cli_activation.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_kill_executor_abort.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_kill_failure_suppression.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_kill_signal_journal.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_kill_worker_stop.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_ladder.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_lint_verb.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_llm_effect.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_main_verb_groups.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_menu_verb_parity.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_merge.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_merge_admission_owner.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_merge_config_local.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_merge_model_resolve.py:5 Rewrites the meta purpose line, and changes owner from engine to clutch/mergequeue.py on line 7, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_mergequeue.py:5 Rewrites the meta purpose line, and changes owner from engine to clutch/mergequeue.py on line 7, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_mergequeue_tree_moved.py:5 Rewrites the meta purpose line, and changes owner from engine to clutch/mergequeue.py on line 7, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_meta_refresh_commit_lock.py:6 Changes owner from engine to clutch/meta.py, and fills the empty purpose on line 4, in a skipped file. (do instead: Put back the base owner and purpose lines.)
- [scope] tests/integration/test_notify.py:4 Rewrites the meta purpose line, and changes owner from engine to clutch/notify.py on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_open_tickets_closed.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_paved_roads.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_policy.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_provider_capture_overwrite.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_provider_cooldown_failover.py:5 Rewrites the meta purpose line, and changes owner on line 7, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_provider_failure_surface.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_providers.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_reconcile.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_regress_scripts_guarded.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_reject_queue.py:5 Rewrites the meta purpose line, and changes owner on line 7, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_reject_reason_both_paths.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_release.py:5 Rewrites the meta purpose line, and changes owner on line 7, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_release_publish.py:5 Rewrites the meta purpose line, and changes owner on line 7, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_reliability_battery.py:5 Rewrites the meta purpose line, and changes owner on line 7, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_requisition.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_requisition_brief_check.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_requisition_gate.py:5 Rewrites the meta purpose line, and changes owner on line 7, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_requisition_identity_record.py:5 Rewrites the meta purpose line, and changes owner on line 7, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_restart_timers.py:5 Rewrites the meta purpose line, and changes owner on line 7, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_retro_box.py:5 Rewrites the meta purpose line, and changes owner on line 7, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_review_command.py:5 Rewrites the meta purpose line, and changes owner on line 7, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_rework.py:5 Rewrites the meta purpose line, and changes owner on line 7, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_rework_failure_terminal_findings.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_rework_supervise.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_roadmap_author.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_roadmap_driver.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_roadmap_gate.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_roadmap_merged.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_roadmap_named_stem.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_roadmap_refile.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_roadmap_row_author.py:5 Rewrites the meta purpose line, and changes owner on line 7, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_roadmap_ship.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_roadmap_start_gates.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_roadmap_status.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_route_kinds_judge_lint.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_scheduler.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_scorecard.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_second_problems.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_serve_admission.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_serve_confirm_during_check.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_serve_dispatch.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_serve_driver.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_serve_driver_overlap.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_serve_kill.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_serve_lifecycle.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_serve_merge_overlap.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_serve_notify.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_serve_parallel_admission.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_serve_scan_head.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_serve_scan_watch_overlap.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_serve_upgrade.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_shakeout.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_snapshot_cache_facts.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_snapshot_merged_cap.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_stale_running.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_stats.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_status.py:5 Rewrites the meta purpose line, and changes owner on line 7, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_step_events.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_step_icons.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_storm.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_storm_hold.py:5 Rewrites the meta purpose line, and changes owner on line 7, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_storm_notification_activation.py:5 Rewrites the meta purpose line, and changes owner on line 7, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_storm_producer.py:5 Rewrites the meta purpose line, and changes owner on line 7, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_supervise_cap_lineage.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_supervisor_rework.py:5 Rewrites the meta purpose line, and changes owner on line 7, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_terminal.py:9 Rewrites the meta purpose line, and changes owner on line 11, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_testguard.py:7 Changes meta owner from engine to clutch/testguard.py in a skipped file. (do instead: Put back the base owner line.)
- [scope] tests/integration/test_testreport.py:4 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_thresh.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_ticket_write_serialization.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_tickets.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_tolerant_reader_callers.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_triage.py:5 Rewrites the meta purpose line, and changes owner on line 7, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_vocabularies.py:5 Rewrites the meta purpose line in a skipped file. (do instead: Put back the base purpose line.)
- [scope] tests/integration/test_vscode_command_not_found.py:5 Rewrites the meta purpose line, and changes owner from engine to vscode-clutchwork on line 7, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_watch.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_watch_surface_tier.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_watchdog.py:4 Rewrites the meta purpose line, and changes owner on line 6, in a skipped file. (do instead: Put back the base purpose and owner lines.)
- [scope] tests/integration/test_watchdog_activation.py:5 Rewrites the meta purpose line, and changes owner on line 7, in a skipped file. (do instead: Put back the base purpose and owner lines.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "71fbb658548e4a9cd946934a94bd71674bb8840e",
  "stem": "disk-io-skip-per-file",
  "reviewed_sha": "71fbb658548e4a9cd946934a94bd71674bb8840e",
  "summary": "The conftest hook, test rewrite, doc sentence and the 184 pytestmark lines are correct, but 181 of the skipped files also get rewritten clutch:meta purpose, owner or relates lines that the ticket forbids ('Nothing else in those files changes'; Definition of rejected: any other changed line), and meta refresh changes only verified/hash, so none of these edits was forced.",
  "findings": [
    {
      "code": "scope",
      "path": "tests/integration/test_ask.py",
      "line": 4,
      "message": "Rewrites the clutch:meta purpose line in a skipped file; the ticket allows only the pytestmark line and `import pytest` to change.",
      "paved_road": "Put back the base-commit purpose line; keep only the marker, the import, and the verified/hash refresh.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_ask_drafts.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_ask_drain_loop.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_ask_drain_loop_agent.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_ask_plan_conduct_covered.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_ask_plan_drain.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_ask_plan_priority_order.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_ask_plan_read_queue.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_ask_plan_serve.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_ask_plan_shared_paths.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_ask_plan_subagent_models.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_ask_roadmap.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_ask_view_events.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_audit.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_author.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_baseline.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_box.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_box_triage_inbox.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_bug_gate.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_caps.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_checkpoint.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_closed_sets.py",
      "line": 11,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_closed_sets_remaining.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_config.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_conflict_rerun_swap.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_context_suggest_cli.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_control.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_control_cli.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_covgate.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_covmap.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_daemon_admission.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_daemon_composition.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_daemon_config.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_daemon_core_queue_seams.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_daemon_pause.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_daemon_soak.py",
      "line": 9,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_daemon_soak_runner.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_daemon_tasks.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_dev.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_dev_vscode_package_kept.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner from engine to dev.py on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_diagnose.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_diagnose_eval.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_doctor.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_drain.py",
      "line": 9,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_drain_admissions.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_drain_containment.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_drain_detach.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_drain_reentry.py",
      "line": 10,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_drain_signals.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_drain_upgrade.py",
      "line": 9,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_driver.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_echo_stage.py",
      "line": 6,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_effects.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_eval_harness.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_evidence_captures_verb.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_evidence_envelope.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_evidence_verbs.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_extension_draw_failure.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_fault_injection.py",
      "line": 12,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_fixture_host.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_flake.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_gates.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_gemini_provider.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_go_ai_panel.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_go_grade.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_handoff_replace.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_harvest.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_harvest_cost_source.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_harvest_orphans.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_heartbeat.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_host_contract.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_host_loop.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_host_mechanical.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_hostfiles.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_hot_paths_snapshot.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_image_candidates_select.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_implement_related_files_prompt.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_inbox.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_index_cli.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_index_extensions.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_index_neighbors_fulltext.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_intake_keeps_draft.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_intake_scope.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_issue_verb.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_kill_cli_activation.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_kill_executor_abort.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_kill_failure_suppression.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_kill_signal_journal.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_kill_worker_stop.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_ladder.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_lint_verb.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_llm_effect.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_main_verb_groups.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_menu_verb_parity.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_merge.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_merge_admission_owner.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_merge_config_local.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_merge_model_resolve.py",
      "line": 5,
      "message": "Rewrites the meta purpose line, and changes owner from engine to clutch/mergequeue.py on line 7, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_mergequeue.py",
      "line": 5,
      "message": "Rewrites the meta purpose line, and changes owner from engine to clutch/mergequeue.py on line 7, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_mergequeue_tree_moved.py",
      "line": 5,
      "message": "Rewrites the meta purpose line, and changes owner from engine to clutch/mergequeue.py on line 7, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_meta_refresh_commit_lock.py",
      "line": 6,
      "message": "Changes owner from engine to clutch/meta.py, and fills the empty purpose on line 4, in a skipped file.",
      "paved_road": "Put back the base owner and purpose lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_notify.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner from engine to clutch/notify.py on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_open_tickets_closed.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_paved_roads.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_policy.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_provider_capture_overwrite.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_provider_cooldown_failover.py",
      "line": 5,
      "message": "Rewrites the meta purpose line, and changes owner on line 7, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_provider_failure_surface.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_providers.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_reconcile.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_regress_scripts_guarded.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_reject_queue.py",
      "line": 5,
      "message": "Rewrites the meta purpose line, and changes owner on line 7, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_reject_reason_both_paths.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_release.py",
      "line": 5,
      "message": "Rewrites the meta purpose line, and changes owner on line 7, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_release_publish.py",
      "line": 5,
      "message": "Rewrites the meta purpose line, and changes owner on line 7, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_reliability_battery.py",
      "line": 5,
      "message": "Rewrites the meta purpose line, and changes owner on line 7, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_requisition.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_requisition_brief_check.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_requisition_gate.py",
      "line": 5,
      "message": "Rewrites the meta purpose line, and changes owner on line 7, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_requisition_identity_record.py",
      "line": 5,
      "message": "Rewrites the meta purpose line, and changes owner on line 7, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_restart_timers.py",
      "line": 5,
      "message": "Rewrites the meta purpose line, and changes owner on line 7, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_retro_box.py",
      "line": 5,
      "message": "Rewrites the meta purpose line, and changes owner on line 7, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_review_command.py",
      "line": 5,
      "message": "Rewrites the meta purpose line, and changes owner on line 7, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_rework.py",
      "line": 5,
      "message": "Rewrites the meta purpose line, and changes owner on line 7, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_rework_failure_terminal_findings.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_rework_supervise.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_roadmap_author.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_roadmap_driver.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_roadmap_gate.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_roadmap_merged.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_roadmap_named_stem.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_roadmap_refile.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_roadmap_row_author.py",
      "line": 5,
      "message": "Rewrites the meta purpose line, and changes owner on line 7, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_roadmap_ship.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_roadmap_start_gates.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_roadmap_status.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_route_kinds_judge_lint.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_scheduler.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_scorecard.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_second_problems.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_serve_admission.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_serve_confirm_during_check.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_serve_dispatch.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_serve_driver.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_serve_driver_overlap.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_serve_kill.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_serve_lifecycle.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_serve_merge_overlap.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_serve_notify.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_serve_parallel_admission.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_serve_scan_head.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_serve_scan_watch_overlap.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_serve_upgrade.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_shakeout.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_snapshot_cache_facts.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_snapshot_merged_cap.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_stale_running.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_stats.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_status.py",
      "line": 5,
      "message": "Rewrites the meta purpose line, and changes owner on line 7, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_step_events.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_step_icons.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_storm.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_storm_hold.py",
      "line": 5,
      "message": "Rewrites the meta purpose line, and changes owner on line 7, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_storm_notification_activation.py",
      "line": 5,
      "message": "Rewrites the meta purpose line, and changes owner on line 7, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_storm_producer.py",
      "line": 5,
      "message": "Rewrites the meta purpose line, and changes owner on line 7, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_supervise_cap_lineage.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_supervisor_rework.py",
      "line": 5,
      "message": "Rewrites the meta purpose line, and changes owner on line 7, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_terminal.py",
      "line": 9,
      "message": "Rewrites the meta purpose line, and changes owner on line 11, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_testguard.py",
      "line": 7,
      "message": "Changes meta owner from engine to clutch/testguard.py in a skipped file.",
      "paved_road": "Put back the base owner line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_testreport.py",
      "line": 4,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_thresh.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_ticket_write_serialization.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_tickets.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_tolerant_reader_callers.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_triage.py",
      "line": 5,
      "message": "Rewrites the meta purpose line, and changes owner on line 7, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_vocabularies.py",
      "line": 5,
      "message": "Rewrites the meta purpose line in a skipped file.",
      "paved_road": "Put back the base purpose line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_vscode_command_not_found.py",
      "line": 5,
      "message": "Rewrites the meta purpose line, and changes owner from engine to vscode-clutchwork on line 7, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_watch.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_watch_surface_tier.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_watchdog.py",
      "line": 4,
      "message": "Rewrites the meta purpose line, and changes owner on line 6, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_watchdog_activation.py",
      "line": 5,
      "message": "Rewrites the meta purpose line, and changes owner on line 7, in a skipped file.",
      "paved_road": "Put back the base purpose and owner lines.",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
