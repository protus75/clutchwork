"""Track migration of hand-built Git seam stand-ins."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tracks migration to GitFake: fails when a test file builds its own Git stand-in without being on the PENDING list, or when a PENDING entry is stale or missing
# relates: [tests/git_fake.py, tests/unit/test_git_fake.py]
# owner: engine
# verified: 452057e3
# hash: f4b19c0bc0d053a0cdace2227d935716a7caec17ca5f65f8729767d40a1bc662

import re
from pathlib import Path

PATTERN = re.compile(
    r"\bgit\s*=\s*(SimpleNamespace|NS|Mock|MagicMock|AsyncMock)\("
    r"|^\s*class\s+(Fake|Empty|Diff)?Git\b"
    r"|spec=Git\b|create_autospec\(Git",
    re.MULTILINE,
)
PENDING = (
    "tests/integration/test_covmap.py",
    "tests/integration/test_harvest_cost_source.py",
    "tests/integration/test_retry_keeps_branch.py",
    "tests/integration/test_serve_verdict_orphan_sweep.py",
    "tests/unit/test_check_meta_fill.py",
    "tests/unit/test_requisition_prior_review.py",
    "tests/unit/test_retro_measurements.py",
    "tests/unit/test_retro_proposal.py",
    "tests/unit/test_retro_recurrence.py",
    "tests/unit/test_review_panel_use.py",
    "tests/unit/test_roadmap_author.py",
    "tests/unit/test_roadmap_merged.py",
    "tests/unit/test_roadmap_merged_parallel.py",
    "tests/unit/test_roadmap_ship.py",
    "tests/unit/test_roadmap_status.py",
    "tests/unit/test_route_kinds_filter.py",
    "tests/unit/test_route_kinds_judge.py",
    "tests/unit/test_run_stages_propagates.py",
    "tests/unit/test_runner_attempt_manifest.py",
    "tests/unit/test_runner_terminal_removal_shield.py",
    "tests/unit/test_runner_verdict_reread.py",
    "tests/unit/test_serve_idle_poll.py",
    "tests/unit/test_serve_verdict_owned.py",
    "tests/unit/test_spool_store_switch.py",
    "tests/unit/test_stages_candidates_select.py",
    "tests/unit/test_stages_conflict_rerun_inputs.py",
    "tests/unit/test_stages_flake_coverage.py",
    "tests/unit/test_stale_running.py",
    "tests/unit/test_supervise_idle_point.py",
    "tests/unit/test_supervisor_trigger.py",
    "tests/unit/test_ticket_lint_rules.py",
    "tests/unit/test_ticket_write_consumers_author.py",
    "tests/unit/test_ticket_write_consumers_runner.py",
    "tests/unit/test_training_eval.py",
    "tests/unit/test_training_export.py",
    "tests/unit/test_training_export_conflict.py",
    "tests/unit/test_training_export_kinds.py",
    "tests/unit/test_training_index_join.py",
    "tests/unit/test_training_ticket_kind.py",
    "tests/unit/test_training_trajectory.py",
    "tests/unit/test_training_triage_records.py",
    "tests/unit/test_verdict_extension.py",
    "tests/unit/test_verdict_menu_parity.py",
)
EXCLUDED = {"tests/unit/test_git_fake.py", "tests/integration/test_git_fake_adoption.py"}


def violations(files, pending):
    return {path for path, content in files.items() if bool(PATTERN.search(content)) != (path in pending)} | (set(pending) - files.keys())


def test_git_fake_adoption():
    root = Path(__file__).resolve().parents[2]
    paths = [p for directory in ("tests/unit", "tests/integration") for p in (root / directory).rglob("*.py")]
    files = {str(p.relative_to(root)): p.read_text() for p in paths if str(p.relative_to(root)) not in EXCLUDED}
    assert not violations(files, PENDING)


def test_adoption_rejects_stale_and_unlisted_entries():
    assert violations({"pending.py": "pass", "new.py": "git = SimpleNamespace("}, ("pending.py",)) == {"pending.py", "new.py"}


def test_adoption_rejects_missing_pending_file():
    assert violations({}, ("missing.py",)) == {"missing.py"}
