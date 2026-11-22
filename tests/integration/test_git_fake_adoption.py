"""Track migration of hand-built Git seam stand-ins."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tracks the move to GitFake. Fails when a test file builds its own Git stand-in but is not on the PENDING list, or when a PENDING entry is stale or missing.
# relates: [tests/git_fake.py, tests/unit/test_git_fake.py]
# owner: engine
# verified: 73ec5da9
# hash: 60fdbb01faf0bc2ccd25a595a26f49ee6e2c6ce9d448df144f22fc19d2ccebbd

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
    "tests/unit/test_runner_verdict_reread.py",
    "tests/unit/test_serve_verdict_owned.py",
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
