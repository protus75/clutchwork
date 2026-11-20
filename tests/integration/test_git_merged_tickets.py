import asyncio
import os
import subprocess
from pathlib import Path

from clutch.git import Git
from clutch.seams import SubprocessExec


def test_first_parent(tmp_path):
    def git(*args):
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "t@example.com"},
        ).stdout.strip()

    git("init")
    shas = []
    for i, message in enumerate(("first\n\nclutch-ticket: a", "second\n\nclutch-ticket: b", "third")):
        (tmp_path / "file").write_text(str(i))
        git("add", "file")
        git("commit", "-m", message)
        shas.append(git("rev-parse", "HEAD"))
    result = asyncio.run(Git(SubprocessExec(), env=os.environ, timeout=10, commit_lock=None).merged_tickets(tmp_path))
    assert result == [(shas[0], "a"), (shas[1], "b")]
