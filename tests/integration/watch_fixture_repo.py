"""Small committed host repository for snapshot integration tests."""

import subprocess
from pathlib import Path

from tests.integration.test_config import VALID


def watch_fixture_repo(tmp_path: Path, state_dir: str) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "config.yaml").write_text(VALID.replace("state_dir: .clutch", f"state_dir: {state_dir}"))
    (repo / "tickets").mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "config.yaml"], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-qm", "fixture"], check=True)
    return repo
