"""Scripted calls distinguish release ordering, isolation, and refusal paths."""

import asyncio
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

from clutch import __main__ as cli
from clutch import release
from clutch.git import Git
from clutch.runner import Refusal

REPO = Path("/repo")
SHA = "abc1234"
STATUS = ["git", "-C", "/repo", "--no-optional-locks", "status", "--porcelain", "--", "pyproject.toml", "uv.lock", "CHANGELOG.md"]


class FakeLock:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class FakeExec:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    async def run(self, argv, *, cwd, env, timeout):
        assert cwd == REPO
        assert env == {"SAFE": "yes"}
        assert 0 < timeout < 100
        self.calls.append(list(argv))
        return self.results.pop(0)


def setup(results=None, version="0.2.0"):
    process = FakeExec(
        results
        if results is not None
        else [
            (0, "", ""),
            (0, f"  {version}\n", ""),
            (1, "", "absent"),
            (128, "", "No names found"),
            (0, "", ""),
            (0, "ignored bump output", ""),
            (0, "", ""),
            (1, "", ""),
            (0, "", ""),
            (0, SHA + "\n", ""),
            (0, "", ""),
        ]
    )
    return process, Git(process, env={"SAFE": "yes"}, timeout=1, commit_lock=FakeLock())


def invoke(process, git, part="minor"):
    fs = SimpleNamespace(read_bytes=lambda path: b"", write=lambda path, data: None)
    return asyncio.run(release.release(REPO, git, process, fs, {"SAFE": "yes"}, part, "2026-01-01"))


def test_minor_release_bumps_commits_and_tags():
    process, git = setup()
    assert invoke(process, git) == ("0.2.0", SHA)
    # Exact trace excludes missing previews, unrestricted commits, premature/lightweight
    # tags, HEAD targets, and a second HEAD read that could pick up an intake commit.
    assert process.calls == [
        STATUS,
        ["uv", "version", "--bump", "minor", "--dry-run", "--short"],
        ["git", "-C", "/repo", "rev-parse", "--verify", "refs/tags/v0.2.0"],
        ["git", "-C", "/repo", "describe", "--tags", "--match", "v*", "--abbrev=0", "HEAD"],
        ["git", "-C", "/repo", "log", "--first-parent", "--format=%s%x00%(trailers:key=clutch-ticket,valueonly)%x1e", "HEAD"],
        ["uv", "version", "--bump", "minor"],
        ["git", "-C", "/repo", "update-index", "--add", "--remove", "--", "pyproject.toml", "uv.lock", "CHANGELOG.md"],
        ["git", "-C", "/repo", "diff", "--cached", "--quiet", "HEAD", "--", "pyproject.toml", "uv.lock", "CHANGELOG.md"],
        ["git", "-C", "/repo", "commit", "-m", "release: 0.2.0", "--only", "--", "pyproject.toml", "uv.lock", "CHANGELOG.md"],
        ["git", "-C", "/repo", "rev-parse", "--verify", "HEAD"],
        ["git", "-C", "/repo", "tag", "-a", "v0.2.0", "-m", "release: 0.2.0", SHA],
    ]
    assert not process.results


def test_patch_release_passes_patch():
    process, git = setup(version="0.1.6")
    assert invoke(process, git, "patch") == ("0.1.6", SHA)
    assert [a for a in process.calls if a[0] == "uv"] == [["uv", "version", "--bump", "patch", "--dry-run", "--short"], ["uv", "version", "--bump", "patch"]]
    assert process.calls[-1] == ["git", "-C", "/repo", "tag", "-a", "v0.1.6", "-m", "release: 0.1.6", SHA]


def test_dirty_version_files_refuse():
    process, git = setup([(0, " M pyproject.toml\n", "")])
    with pytest.raises(Refusal, match="pyproject.toml"):
        invoke(process, git)
    assert process.calls == [STATUS]


def test_existing_tag_refuses():
    process, git = setup([(0, "", ""), (0, "0.2.0\n", ""), (0, "old-sha", "")])
    with pytest.raises(Refusal, match="v0.2.0"):
        invoke(process, git)
    assert process.calls == [STATUS, ["uv", "version", "--bump", "minor", "--dry-run", "--short"], ["git", "-C", "/repo", "rev-parse", "--verify", "refs/tags/v0.2.0"]]


@pytest.mark.parametrize("bump,stderr", [(False, "warning\nerror: No version field found\n\n"), (True, "warning\nerror: lock failed\n\n"), (False, ""), (True, "")])
def test_uv_failure_refuses(bump, stderr):
    results = [(0, "", "")]
    if bump:
        results += [(0, "0.2.0", ""), (1, "", "absent"), (128, "", "No names found"), (0, "", "")]
    results += [(1 if bump else 2, "", stderr)]
    process, git = setup(results)
    with pytest.raises(Refusal) as error:
        invoke(process, git)
    assert (stderr.strip().splitlines()[-1] if stderr else "failed") in str(error.value)
    if bump:
        assert "restore pyproject.toml and uv.lock" in str(error.value)
    assert len(process.calls) == (6 if bump else 2)
    assert process.calls[-1] == ["uv", "version", "--bump", "minor", *([] if bump else ["--dry-run", "--short"])]


def test_git_tag_argv():
    process, git = setup([(0, "", "")])
    asyncio.run(git.tag(REPO, "v0.2.0", "release: 0.2.0", SHA))
    assert process.calls == [["git", "-C", "/repo", "tag", "-a", "v0.2.0", "-m", "release: 0.2.0", SHA]]
    process.calls.clear()
    for name, target in [("-f", SHA), ("v0.2.0", "-f")]:
        with pytest.raises(ValueError):
            asyncio.run(git.tag(REPO, name, "message", target))
    assert process.calls == []


def test_parser_requires_one_part():
    for argv in [[], ["--minor", "--patch"], ["--major"]]:
        with pytest.raises(SystemExit):
            cli._parser().parse_args(["release", "bump", *argv])
    for part in ["minor", "patch"]:
        assert cli._parser().parse_args(["release", "bump", "--" + part]).part == part


@pytest.mark.parametrize("refuse", [False, True])
def test_main_release_locks_calls_and_prints(monkeypatch, capsys, refuse):
    events = []
    monkeypatch.setattr(cli, "load_config", lambda *a, **kw: SimpleNamespace(state_dir=Path("/state")))
    monkeypatch.setattr(cli, "child_env", lambda *a: {"SAFE": "yes"})

    class Lock:
        def __init__(self, state_dir, *, verb, instance_id, clock):
            assert (state_dir, verb, instance_id) == (Path("/state"), "release", "description")

        def acquire(self):
            events.append("acquire")

        def release(self):
            events.append("unlock")

    async def describe(self, repo):
        assert repo == REPO
        return "description"

    async def fake_release(repo, git, process, fs, env, part, today):
        assert fs is not None and date.fromisoformat(today)
        assert repo == REPO and isinstance(git, Git) and isinstance(process, cli.SubprocessExec)
        assert env == {"SAFE": "yes"}
        events.append(part)
        if refuse:
            raise Refusal("blocked", "repair")
        return "0.2.0", SHA

    monkeypatch.setattr(cli, "Journal", lambda *a: SimpleNamespace(append=lambda *a, **kw: None))
    monkeypatch.setattr(cli, "Lockfile", Lock)
    monkeypatch.setattr(Git, "describe", describe)
    monkeypatch.setattr(release, "release", fake_release)
    assert cli.main(["release", "bump", "--minor"], cwd=REPO, env={}) == (2 if refuse else 0)
    captured = capsys.readouterr()
    assert captured.out == ("" if refuse else f"release: tagged v0.2.0 at {SHA}\n")
    assert captured.err == ("clutch release: blocked -- repair\n" if refuse else "")
    assert events == ["acquire", "minor", "unlock"]
