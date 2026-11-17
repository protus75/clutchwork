import asyncio
from pathlib import Path

import pytest

from clutch.git import Git, GitError
from clutch.release import release
from clutch.runner import Refusal


class Process:
    def __init__(self, output=""):
        self.calls = []
        self.output = output

    async def run(self, argv, **kwargs):
        self.calls.append(argv)
        if argv[0] == "uv":
            return 0, "0.4.0", ""
        return 0, self.output, ""


class FS:
    def __init__(self, events):
        self.events = events

    def read_bytes(self, path):
        raise FileNotFoundError(path)

    def write(self, path, data):
        self.events.append(("write", path.name, data))


class FakeGit:
    def __init__(self, previous=None, dirty="", exists=False):
        self.previous = previous
        self.dirty = dirty
        self.exists = exists
        self.events = []

    async def status_porcelain(self, repo, *paths):
        assert "CHANGELOG.md" in paths
        return self.dirty

    async def rev_parse(self, repo, ref):
        if self.exists:
            return "existing"
        raise GitError([], 1, "", "missing")

    async def previous_release_tag(self, repo):
        return self.previous

    async def merged_subjects(self, repo, since):
        self.events.append(("since", since))
        return ["clutch(a-b): Does X. Also Y."]

    async def commit(self, repo, message, *, only):
        self.events.append(("commit", message, only))
        return "sha"

    async def tag(self, repo, tag, message, sha):
        self.events.append(("tag", tag, sha))


@pytest.mark.parametrize("previous", [None, "v0.3.0"])
def test_release_writes_before_commit(previous):
    git = FakeGit(previous)
    process = Process()
    assert asyncio.run(release(Path("/repo"), git, process, FS(git.events), {}, "minor", "2026-02-03")) == ("0.4.0", "sha")
    assert git.events == [
        ("since", previous),
        ("write", "CHANGELOG.md", b"# Changelog\n\n## 0.4.0 - 2026-02-03\n- a-b: Does X.\n"),
        ("commit", "release: 0.4.0", ["pyproject.toml", "uv.lock", "CHANGELOG.md"]),
        ("tag", "v0.4.0", "sha"),
    ]


@pytest.mark.parametrize("dirty,exists", [(" M CHANGELOG.md", False), ("", True)])
def test_refusals_before_write(dirty, exists):
    git = FakeGit(dirty=dirty, exists=exists)
    process = Process()
    with pytest.raises(Refusal):
        asyncio.run(release(Path("/repo"), git, process, FS(git.events), {}, "minor", "2026-02-03"))
    assert git.events == []
    assert process.calls == ([] if dirty else [["uv", "version", "--bump", "minor", "--dry-run", "--short"]])


@pytest.mark.parametrize("since,revision", [(None, "HEAD"), ("v0.3.0", "v0.3.0..HEAD")])
def test_merged_subjects_filters_trailers(since, revision):
    process = Process("clutch(a-b): Does X.\0a-b\n\x1e\nclutch(a-b): review\0\x1e\n")
    git = Git(process, env={}, timeout=1, commit_lock=None)
    assert asyncio.run(git.merged_subjects(Path("/repo"), since)) == ["clutch(a-b): Does X."]
    assert process.calls == [["git", "-C", "/repo", "log", "--first-parent", "--format=%s%x00%(trailers:key=clutch-ticket,valueonly)%x1e", revision]]
