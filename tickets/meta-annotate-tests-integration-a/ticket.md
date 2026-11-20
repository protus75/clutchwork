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
`meta-schema-and-refresh-r2` ships `clutch meta refresh` and `clutch meta check` and the `meta.paths` roots in `config.yaml`. After this ticket the 113 tracked `.md` and `.py` files in the first half of `tests/integration/` by file name each carry a valid `clutch.meta/1.0` block, so `uv run clutch meta check` on exactly those files exits 0.

Why: the first attempt at `meta-schema-and-refresh-r2` annotated about 600 files in one diff of 5512 inserted lines and failed the 1500-line diff budget (`diagnosis.json`, verdict split). This ticket is one shard of that work, sized under the budget at about 9 inserted lines per file, so it can merge.

## Boundary contract
none
- reason: metadata only; each file gains a comment block that no code or test reads, produced by the unchanged `clutch meta refresh`, and no behavior, parser or consumer changes

## Scope in / Scope out
In: run `uv run clutch meta refresh` on exactly the files listed in `## Scope fence`, then give each block a non-empty `purpose`, because refresh inserts it empty and `meta check` reports `empty_purpose` for that. `meta fill` does not exist and is out of scope, so purposes are set with a throwaway script that is not committed and not fenced. Purpose rule, applied to every file the same way: for a `.py` file, the first line of its module docstring, else the file stem with `_` and `-` replaced by spaces; for a `.md` file, the text of its first `#` heading, else the file stem with `-` replaced by spaces; cut to at most 120 characters and never empty. Do not edit `relates`, `owner`, `kind`, `verified` or `hash` by hand. Refresh keeps every generated `# relates:` line within the line length that `meta-schema-and-refresh-r2` fixes, so no lint exemption is added and `pyproject.toml` is not touched. A file that fails `ruff` or an existing test only because of its new block is fixed in the block, never by editing the file's body.

Out: every other file, `clutch/specs/`, `meta fill`, the `meta_drift` gate, Check-time refresh, and any change to `config.yaml` (the roots are set by `meta-schema-and-refresh-r2`).

## Scope fence
- tests/integration/__init__.py
- tests/integration/conftest.py
- tests/integration/serve_rig.py
- tests/integration/test_acceptance_spec.py
- tests/integration/test_ask.py
- tests/integration/test_ask_drafts.py
- tests/integration/test_ask_drain_loop.py
- tests/integration/test_ask_drain_loop_agent.py
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_ask_plan_serve.py
- tests/integration/test_ask_roadmap.py
- tests/integration/test_ask_view_events.py
- tests/integration/test_audit.py
- tests/integration/test_author.py
- tests/integration/test_authoring_document_test_rule.py
- tests/integration/test_baseline.py
- tests/integration/test_boundary_contract_spec_rules.py
- tests/integration/test_box.py
- tests/integration/test_box_triage_inbox.py
- tests/integration/test_bug_gate.py
- tests/integration/test_callmeter_no_provider_names.py
- tests/integration/test_caps.py
- tests/integration/test_changelog_url.py
- tests/integration/test_checkpoint.py
- tests/integration/test_cli.py
- tests/integration/test_closed_sets.py
- tests/integration/test_closed_sets_remaining.py
- tests/integration/test_closed_sets_single_owner.py
- tests/integration/test_config.py
- tests/integration/test_conflict_rerun_swap.py
- tests/integration/test_contention_rules.py
- tests/integration/test_control.py
- tests/integration/test_control_cli.py
- tests/integration/test_core_supervisor_verdicts.py
- tests/integration/test_covgate.py
- tests/integration/test_covmap.py
- tests/integration/test_daemon_admission.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_daemon_config.py
- tests/integration/test_daemon_core_queue_seams.py
- tests/integration/test_daemon_pause.py
- tests/integration/test_daemon_soak.py
- tests/integration/test_daemon_soak_runner.py
- tests/integration/test_daemon_tasks.py
- tests/integration/test_dev.py
- tests/integration/test_dev_vscode_package_kept.py
- tests/integration/test_diagnose.py
- tests/integration/test_diagnose_eval.py
- tests/integration/test_diagnose_spec_json_reply.py
- tests/integration/test_doctor.py
- tests/integration/test_drain.py
- tests/integration/test_drain_admissions.py
- tests/integration/test_drain_containment.py
- tests/integration/test_drain_detach.py
- tests/integration/test_drain_eligible_callers.py
- tests/integration/test_drain_reentry.py
- tests/integration/test_drain_signals.py
- tests/integration/test_drain_upgrade.py
- tests/integration/test_driver.py
- tests/integration/test_driver_overwrite_source.py
- tests/integration/test_echo_stage.py
- tests/integration/test_effects.py
- tests/integration/test_engine_text_verbs.py
- tests/integration/test_eval_harness.py
- tests/integration/test_evidence_claude_fixture.py
- tests/integration/test_evidence_codex_fixture.py
- tests/integration/test_evidence_envelope.py
- tests/integration/test_evidence_gemini_fixture.py
- tests/integration/test_exec_seam_reap.py
- tests/integration/test_exec_seam_unwind_capture.py
- tests/integration/test_extension_argv.py
- tests/integration/test_extension_draw_failure.py
- tests/integration/test_fault_injection.py
- tests/integration/test_fence_closure_registries.py
- tests/integration/test_fixture_host.py
- tests/integration/test_flake.py
- tests/integration/test_fs_seam_sites.py
- tests/integration/test_gate_floors.py
- tests/integration/test_gates.py
- tests/integration/test_gemini_provider.py
- tests/integration/test_git.py
- tests/integration/test_git_merged_tickets.py
- tests/integration/test_git_tree_id.py
- tests/integration/test_go_ai_panel.py
- tests/integration/test_go_grade.py
- tests/integration/test_graphics_review_spec_blocks.py
- tests/integration/test_handoff_replace.py
- tests/integration/test_harvest.py
- tests/integration/test_harvest_cost_source.py
- tests/integration/test_harvest_orphans.py
- tests/integration/test_heartbeat.py
- tests/integration/test_help.py
- tests/integration/test_host_contract.py
- tests/integration/test_host_loop.py
- tests/integration/test_host_mechanical.py
- tests/integration/test_host_onboarding_doc.py
- tests/integration/test_hostfiles.py
- tests/integration/test_hot_paths_snapshot.py
- tests/integration/test_image_candidates_select.py
- tests/integration/test_implement_spec_keep_editing.py
- tests/integration/test_implement_spec_mutation_check.py
- tests/integration/test_inbox.py
- tests/integration/test_intake_keeps_draft.py
- tests/integration/test_intake_scope.py
- tests/integration/test_issue_verb.py
- tests/integration/test_journal.py
- tests/integration/test_journal_duckdb_cache.py
- tests/integration/test_journal_incremental.py
- tests/integration/test_journal_roll.py
- tests/integration/test_kill_cli_activation.py
- tests/integration/test_kill_executor_abort.py
- tests/integration/test_kill_failure_suppression.py
- tests/integration/test_kill_signal_journal.py

## Acceptance criteria
1. Each of the 113 files in `## Scope fence` starts a valid block with a matching hash and a non-empty `purpose`, so `uv run clutch meta check` on those files exits 0 with no `missing`, `empty_purpose`, `drifted` or `malformed` finding, not just a pass because it was given an empty list. Check: `uv run clutch meta check` over the same paths as `## Verification`.
2. The diff inserts fewer than 1500 lines and deletes none, and each changed file differs from its base only by its block. Check: `./dev.py test` in `## Verification` and the Check stage's `diff_budget` gate.
3. No file outside `## Scope fence` changes, and no `.md` file with frontmatter loses `---` at byte 0. Check: `./dev.py test` in `## Verification`.

## Verification
```
uv run clutch meta check tests/integration/__init__.py tests/integration/conftest.py tests/integration/serve_rig.py tests/integration/test_acceptance_spec.py tests/integration/test_ask.py tests/integration/test_ask_drafts.py tests/integration/test_ask_drain_loop.py tests/integration/test_ask_drain_loop_agent.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_serve.py tests/integration/test_ask_roadmap.py tests/integration/test_ask_view_events.py tests/integration/test_audit.py tests/integration/test_author.py tests/integration/test_authoring_document_test_rule.py tests/integration/test_baseline.py tests/integration/test_boundary_contract_spec_rules.py tests/integration/test_box.py tests/integration/test_box_triage_inbox.py tests/integration/test_bug_gate.py tests/integration/test_callmeter_no_provider_names.py tests/integration/test_caps.py tests/integration/test_changelog_url.py tests/integration/test_checkpoint.py tests/integration/test_cli.py tests/integration/test_closed_sets.py tests/integration/test_closed_sets_remaining.py tests/integration/test_closed_sets_single_owner.py tests/integration/test_config.py tests/integration/test_conflict_rerun_swap.py tests/integration/test_contention_rules.py tests/integration/test_control.py tests/integration/test_control_cli.py tests/integration/test_core_supervisor_verdicts.py tests/integration/test_covgate.py tests/integration/test_covmap.py tests/integration/test_daemon_admission.py tests/integration/test_daemon_composition.py tests/integration/test_daemon_config.py tests/integration/test_daemon_core_queue_seams.py tests/integration/test_daemon_pause.py tests/integration/test_daemon_soak.py tests/integration/test_daemon_soak_runner.py tests/integration/test_daemon_tasks.py tests/integration/test_dev.py tests/integration/test_dev_vscode_package_kept.py tests/integration/test_diagnose.py tests/integration/test_diagnose_eval.py tests/integration/test_diagnose_spec_json_reply.py tests/integration/test_doctor.py tests/integration/test_drain.py tests/integration/test_drain_admissions.py tests/integration/test_drain_containment.py tests/integration/test_drain_detach.py tests/integration/test_drain_eligible_callers.py tests/integration/test_drain_reentry.py tests/integration/test_drain_signals.py tests/integration/test_drain_upgrade.py tests/integration/test_driver.py tests/integration/test_driver_overwrite_source.py tests/integration/test_echo_stage.py tests/integration/test_effects.py tests/integration/test_engine_text_verbs.py tests/integration/test_eval_harness.py tests/integration/test_evidence_claude_fixture.py tests/integration/test_evidence_codex_fixture.py tests/integration/test_evidence_envelope.py tests/integration/test_evidence_gemini_fixture.py tests/integration/test_exec_seam_reap.py tests/integration/test_exec_seam_unwind_capture.py tests/integration/test_extension_argv.py tests/integration/test_extension_draw_failure.py tests/integration/test_fault_injection.py tests/integration/test_fence_closure_registries.py tests/integration/test_fixture_host.py tests/integration/test_flake.py tests/integration/test_fs_seam_sites.py tests/integration/test_gate_floors.py tests/integration/test_gates.py tests/integration/test_gemini_provider.py tests/integration/test_git.py tests/integration/test_git_merged_tickets.py tests/integration/test_git_tree_id.py tests/integration/test_go_ai_panel.py tests/integration/test_go_grade.py tests/integration/test_graphics_review_spec_blocks.py tests/integration/test_handoff_replace.py tests/integration/test_harvest.py tests/integration/test_harvest_cost_source.py tests/integration/test_harvest_orphans.py tests/integration/test_heartbeat.py tests/integration/test_help.py tests/integration/test_host_contract.py tests/integration/test_host_loop.py tests/integration/test_host_mechanical.py tests/integration/test_host_onboarding_doc.py tests/integration/test_hostfiles.py tests/integration/test_hot_paths_snapshot.py tests/integration/test_image_candidates_select.py tests/integration/test_implement_spec_keep_editing.py tests/integration/test_implement_spec_mutation_check.py tests/integration/test_inbox.py tests/integration/test_intake_keeps_draft.py tests/integration/test_intake_scope.py tests/integration/test_issue_verb.py tests/integration/test_journal.py tests/integration/test_journal_duckdb_cache.py tests/integration/test_journal_incremental.py tests/integration/test_journal_roll.py tests/integration/test_kill_cli_activation.py tests/integration/test_kill_executor_abort.py tests/integration/test_kill_failure_suppression.py tests/integration/test_kill_signal_journal.py
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
- reason: one mechanical refresh plus a purpose pass over about 113 files; they share one command and the Check stage proves them together, so they cannot merge separately.
