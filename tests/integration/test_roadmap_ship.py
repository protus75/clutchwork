# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that clutch release ship passes the roadmap gate, bumps, commits and tags the release, then stops at the next failing gate and refuses a dirty tree
# relates: [clutch/config.py, clutch/git.py, clutch/journal.py, clutch/roadmap.py, clutch/runner.py, clutch/seams.py, tests/integration/test_cli.py]
# owner: clutch/roadmap.py
# verified: 62a64dee
# hash: bf3f9757a3866e46561a83cbab62723127456ca7a68b91a5c24081dade075e46
import asyncio
import shlex
import sys
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from clutch import __main__ as cli
from clutch import config, roadmap
from clutch.git import CommitLock, Git, GitError
from clutch.journal import Journal
from clutch.runner import Refusal
from clutch.seams import LocalFileSystem, SubprocessExec
from tests.cli_helpers import CONFIG, ENV

pytestmark = pytest.mark.disk_io_skip


def test_ship_releases_then_waits_for_the_next_gate(tmp_path, monkeypatch, capsys):
    def clock():
        return datetime(2026, 1, 1, tzinfo=UTC)

    original = SubprocessExec.run
    uv_calls = []

    async def execute(self, argv, **kwargs):
        if argv[0] != "uv":
            return await original(self, argv, **kwargs)
        uv_calls.append(argv)
        if "--dry-run" in argv:
            return 0, "1.1.0\n", ""
        for name in ("pyproject.toml", "uv.lock"):
            path = kwargs["cwd"] / name
            path.write_text(path.read_text().replace("1.0.0", "1.1.0"))
        return 0, "", ""

    monkeypatch.setattr(SubprocessExec, "run", execute)

    def repository(repo, upload=False):
        repo.mkdir()
        git = Git(SubprocessExec(), env=ENV, timeout=10, commit_lock=CommitLock(repo / ".clutch/state", clock=clock, sleep=asyncio.sleep))

        def call(*args):
            return asyncio.run(git._run(repo, *args)).strip()

        asyncio.run(git.init(repo, branch="main"))
        (repo / "config.yaml").write_text(CONFIG + ("release: {publish: true, pypi_token: TOKEN}\n" if upload else ""))
        (repo / "pyproject.toml").write_text('[project]\nname="host"\nversion="1.0.0"\n')
        (repo / "uv.lock").write_text('version = "1.0.0"\n')
        (repo / "tracked").write_text("original")
        path = repo / roadmap.ROADMAP
        path.parent.mkdir()
        header = "| # | Stem | Owner | Kind | P | Depends on | Runs before | Content |\n|---|---|---|---|---|---|---|---|\n"
        path.write_text(
            "### 1.1.0\n"
            + header
            + "| 1 | `one` | roadmap | feature | P1 | | | one |\n```gate\n"
            + shlex.join([sys.executable, "-c", "pass"])
            + "\n```\n### 1.2.0\n"
            + header
            + "| 2 | `two` | roadmap | feature | P1 | | | two |\n```gate\n"
            + shlex.join([sys.executable, "-c", "raise SystemExit(1)"])
            + "\n```\n"
        )
        asyncio.run(git.add(repo, ["config.yaml", "pyproject.toml", "uv.lock", "tracked", roadmap.ROADMAP]))
        asyncio.run(git.commit(repo, "initial"))
        cfg = config.load_config(None, cwd=repo)
        journal = Journal(repo / ".clutch/state", clock)
        return SimpleNamespace(repo=repo, git=git, exec_=SubprocessExec(), fs=LocalFileSystem(), env={**ENV, "TOKEN": "secret"}, config=cfg, journal=journal, clock=clock), call

    c, call = repository(tmp_path / "first")
    assert cli.main(["release", "ship"], cwd=c.repo, env=c.env, clock=clock) == 0
    lines = capsys.readouterr().out.splitlines()
    head = call("rev-parse", "HEAD")
    assert lines[-2:] == ["gate 1.1.0: passed", f"release: tagged v1.1.0 at {head}"]
    assert call("show", "-s", "--format=%s", "HEAD") == "release: 1.1.0"
    assert call("rev-parse", "v1.1.0^{commit}") == head
    assert [e.body for e in c.journal.read()] == [
        {"signal": "roadmap_gate", "release": "1.1.0", "passed": True, "failed": None},
        {"signal": "release", "version": "1.1.0", "tag": "v1.1.0", "commit": head},
    ]
    assert uv_calls == [["uv", "version", "--bump", "minor", "--dry-run", "--short"], ["uv", "version", "--bump", "minor"]]
    assert cli.main(["release", "ship"], cwd=c.repo, env=c.env, clock=clock) == 1
    assert capsys.readouterr().out.splitlines()[-1] == "gate 1.2.0: failed"
    assert call("rev-parse", "HEAD") == head and call("tag", "--list") == "v1.1.0"
    dirty, dirty_call = repository(tmp_path / "dirty", True)
    before = dirty_call("rev-parse", "HEAD")
    (dirty.repo / "tracked").write_text("changed")
    assert cli.main(["release", "ship"], cwd=dirty.repo, env=dirty.env, clock=clock) == 2
    assert "uncommitted tracked files" in capsys.readouterr().err
    assert dirty_call("rev-parse", "HEAD") == before and dirty_call("tag", "--list") == ""
    assert [e.body["signal"] for e in dirty.journal.read()] == ["roadmap_gate"]
