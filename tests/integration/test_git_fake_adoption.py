"""Track migration of hand-built Git seam stand-ins."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Fails when any unit or integration test builds its own Git stand-in or uses the old FakeGit instead of the shared GitFake
# relates: [tests/git_fake.py, tests/unit/test_git_fake.py]
# owner: engine
# verified: 10f08d74
# hash: fb57c40dff3085cab0bf9ea49cc211ac6268e6daa4feb69367fbd333de3d1bfe

import re
from pathlib import Path

PATTERN = re.compile(
    r"\bgit\s*=\s*(SimpleNamespace|NS|Mock|MagicMock|AsyncMock)\("
    r"|^\s*class\s+(Fake|Empty|Diff)?Git\b"
    r"|spec=Git\b|create_autospec\(Git"
    r"|\b(?:FakeGit|fake_git)\b",
    re.MULTILINE,
)
EXCLUDED = {"tests/unit/test_git_fake.py", "tests/integration/test_git_fake_adoption.py"}


def violations(files):
    return {path for path, content in files.items() if PATTERN.search(content)}


def test_git_fake_adoption():
    root = Path(__file__).resolve().parents[2]
    paths = [p for directory in ("tests/unit", "tests/integration") for p in (root / directory).rglob("*.py")]
    files = {str(p.relative_to(root)): p.read_text() for p in paths if str(p.relative_to(root)) not in EXCLUDED}
    assert not violations(files)


def test_adoption_rejects_stand_in():
    assert violations({"stand_in.py": "git = SimpleNamespace("}) == {"stand_in.py"}


def test_adoption_rejects_old_fake():
    assert violations({"old.py": "from tests.fakes import FakeGit"}) == {"old.py"}
