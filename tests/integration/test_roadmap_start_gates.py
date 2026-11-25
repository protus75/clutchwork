# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that roadmap start gates hold back status and author-ahead until they pass, and checks the repository's start and ship gate blocks.
# relates: [clutch/box.py, clutch/config.py, clutch/git.py, clutch/journal.py, clutch/lockfile.py, clutch/roadmap.py, clutch/seams.py]
# owner: clutch/roadmap.py
# verified: 62a64dee
# hash: 70f1bb8e39a2375505181ffa329ed1ec03e676118fc96be8ed3dd6f3033142cb
import asyncio
import shlex
import sys
from pathlib import Path

import pytest

from clutch import roadmap
from clutch.box import Box
from clutch.config import load_config
from clutch.journal import Journal
from clutch.seams import LocalFileSystem, SubprocessExec
from tests.cli_helpers import ENV
from tests.drain_helpers import Clock
from tests.integration.test_roadmap_author import setup_repo
from tests.unit.test_roadmap_status import fixture

pytestmark = pytest.mark.disk_io_skip


def test_status_and_author_start(tmp_path, monkeypatch):
    status_root = tmp_path / "status"
    status_root.mkdir()
    c, _, _, _ = fixture(status_root)
    path = status_root / roadmap.ROADMAP
    command = shlex.join([sys.executable, "-c", "raise SystemExit(3)"])
    path.write_text(path.read_text().replace("### 1.0.0\n", f"### 1.0.0\n```start\n{command}\n```\n", 1))
    c.exec_ = SubprocessExec()
    c.env = {}
    c.config.drain = type("Drain", (), {"max_ticket_minutes": 1})()
    monkeypatch.setattr(roadmap, "child_env", lambda *args: {})
    lines = asyncio.run(roadmap.status(c))
    assert any(line.startswith(f"waits: row 11 q-eleven: start gate of 1.0.0 fails: {command}") for line in lines)
    assert "next: none" in lines

    (tmp_path / "author").mkdir()
    root, journal = setup_repo(tmp_path / "author")
    path = root / roadmap.ROADMAP
    original = path.read_text()
    path.write_text(original.replace("### Next\n", f"### Next\n```start\n{command}\n```\n", 1))
    from tests.cli_helpers import git_out

    git_out(root, "add", "docs/roadmap.md")
    git_out(root, "commit", "-m", "add start gate")
    from clutch.git import Git
    from clutch.lockfile import CommitLock

    config = load_config(None, cwd=root)
    checkout = type(
        "Checkout",
        (),
        {
            "repo": root,
            "git": Git(SubprocessExec(), env=ENV, timeout=10, commit_lock=CommitLock(config.state_dir, clock=Clock(), sleep=asyncio.sleep)),
            "journal": journal,
            "config": config,
            "fs": LocalFileSystem(),
            "exec_": SubprocessExec(),
            "env": {},
        },
    )()
    called = []

    async def author(ids):
        called.extend(ids)

    asyncio.run(roadmap.author_ahead(checkout, 1, author))
    box = Box(config.state_dir / "box", checkout.fs)
    assert not [m for m in box.messages() if m.message_class == "roadmap_row"]
    assert called == []
    path.write_text(path.read_text().replace(command, shlex.join([sys.executable, "-c", "pass"])))
    git_out(root, "add", "docs/roadmap.md")
    git_out(root, "commit", "-m", "pass start gate")
    asyncio.run(roadmap.author_ahead(checkout, 1, author))
    assert len([m for m in box.messages() if m.message_class == "roadmap_row"]) == 1
    assert len(called) == 1


def test_repository_start_and_ship_blocks():
    text = (Path(__file__).resolve().parents[2] / roadmap.ROADMAP).read_text()
    assert roadmap.gates(text, "start") == {
        "0.5.0": (("uv", "run", "clutch", "roadmap", "merged", "closed-sets-single-owner", "active-slot-single-owner", "merge-admission-single-owner"),),
        "0.7.0": (("uv", "run", "clutch", "roadmap", "merged", "--release", "0.6.0", "--since", "v0.6.0", "--at-least", "1"),),
        "0.8.0": (("uv", "run", "clutch", "roadmap", "merged", "--release", "0.7.0", "--since", "v0.7.0", "--at-least", "1"),),
        "0.9.0": (("uv", "run", "clutch", "roadmap", "merged", "--release", "0.8.0", "--since", "v0.8.0", "--at-least", "1"),),
    }
    assert set(roadmap.gates(text, "gate")) == {"0.4.0", "0.5.0", "0.6.0", "0.7.0", "0.8.0", "0.9.0"}
