"""Real git proves the release preserves unrelated staged and unstaged edits."""

import asyncio
from datetime import UTC, datetime

import pytest

from clutch.__main__ import main
from clutch.git import Git
from clutch.lockfile import CommitLock, Lockfile
from clutch.seams import SubprocessExec
from tests.integration.test_cli import CONFIG, ENV


def clock():
    return datetime(2026, 1, 1, tzinfo=UTC)


@pytest.fixture
def repository(tmp_path, monkeypatch):
    git = Git(SubprocessExec(), env=ENV, timeout=10, commit_lock=CommitLock(tmp_path / ".clutch/state", clock=clock, sleep=asyncio.sleep))

    def call(*args):
        return asyncio.run(git._run(tmp_path, *args)).strip()

    asyncio.run(git.init(tmp_path, branch="main"))
    for name, text in [
        ("config.yaml", CONFIG),
        ("pyproject.toml", '[project]\nname = "host"\nversion = "0.1.5"\n'),
        ("uv.lock", 'version = "0.1.5"\n'),
        ("modified", "original"),
        ("staged", "original"),
    ]:
        (tmp_path / name).write_text(text)
    asyncio.run(git.add(tmp_path, ["config.yaml", "pyproject.toml", "uv.lock", "modified", "staged"]))
    asyncio.run(git.commit(tmp_path, "initial"))
    (tmp_path / "modified").write_text("unstaged edit")
    (tmp_path / "staged").write_text("staged edit")
    asyncio.run(git.add(tmp_path, ["staged"]))
    original_run = SubprocessExec.run
    uv_calls = []

    async def run(self, argv, **kwargs):
        if argv[0] != "uv":
            return await original_run(self, argv, **kwargs)
        uv_calls.append(list(argv))
        if "--dry-run" in argv:
            return 0, "0.2.0\n", ""
        for name in ["pyproject.toml", "uv.lock"]:
            path = tmp_path / name
            path.write_text(path.read_text().replace("0.1.5", "0.2.0"))
        return 0, "deliberately not a version", ""

    monkeypatch.setattr(SubprocessExec, "run", run)
    return tmp_path, git, call, uv_calls


def test_release_commits_and_tags(repository, capsys):
    repo, git, call, uv_calls = repository
    old_head = call("rev-parse", "HEAD")
    assert main(["release", "--minor"], cwd=repo, env=ENV) == 0
    sha = call("rev-parse", "HEAD")
    assert sha != old_head
    assert capsys.readouterr().out == f"release: tagged v0.2.0 at {sha}\n"
    assert call("show", "-s", "--format=%s", "HEAD") == "release: 0.2.0"
    assert call("show", "--name-only", "--format=", "HEAD").splitlines() == ["pyproject.toml", "uv.lock"]
    assert call("cat-file", "-t", "v0.2.0") == "tag"
    assert call("rev-parse", "v0.2.0^{commit}") == sha
    assert call("diff", "--name-only") == "modified"
    assert call("diff", "--cached", "--name-only") == "staged"
    assert (repo / "modified").read_text() == "unstaged edit"
    assert (repo / "staged").read_text() == "staged edit"
    assert call("show", "HEAD:modified") == "original"
    assert call("show", "HEAD:staged") == "original"
    assert uv_calls == [["uv", "version", "--bump", "minor", "--dry-run", "--short"], ["uv", "version", "--bump", "minor"]]


@pytest.mark.parametrize("reason", ["dirty", "tag", "lock"])
def test_release_refusals_change_nothing(repository, capsys, reason):
    repo, git, call, uv_calls = repository
    lock = Lockfile(repo / ".clutch/state", verb="test", instance_id="test", clock=clock)
    if reason == "dirty":
        (repo / "pyproject.toml").write_text("dirty version file")
    elif reason == "tag":
        asyncio.run(git.tag(repo, "v0.2.0", "existing release", call("rev-parse", "HEAD")))
    else:
        lock.acquire()

    def snapshot():
        return call("rev-parse", "HEAD"), call("tag", "--list"), [(repo / name).read_bytes() for name in ["pyproject.toml", "uv.lock"]]

    before = snapshot()
    try:
        assert main(["release", "--minor"], cwd=repo, env=ENV) == 2
    finally:
        if lock.held:
            lock.release()
    captured = capsys.readouterr()
    assert captured.err.startswith("clutch release:")
    assert captured.out == ""
    assert snapshot() == before
    if reason == "lock":
        assert "clutch.lock" in captured.err
    assert uv_calls == ([["uv", "version", "--bump", "minor", "--dry-run", "--short"]] if reason == "tag" else [])
