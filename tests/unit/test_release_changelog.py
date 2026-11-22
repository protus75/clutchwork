# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Release writes the CHANGELOG before the commit and tag, refuses on a dirty changelog or an existing tag, and merged_subjects filters out trailer commits
# relates: [clutch/git.py, clutch/release.py, clutch/runner.py]
# owner: engine
# verified: 452057e3
# hash: 8a04678e9836ee2d33c9556765c0d34aff456617734175da108eedb21a4380e7
import asyncio
from pathlib import Path

import pytest

from clutch.git import Git, GitError
from clutch.release import release
from clutch.runner import Refusal
from tests.git_fake import GitFake


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


def make_git(previous=None, dirty="", exists=False):
    events = []

    def status(repo, *paths):
        assert "CHANGELOG.md" in paths
        return dirty

    def rev_parse(repo, ref):
        if exists:
            return "existing"
        raise GitError([], 1, "", "missing")

    def subjects(repo, since):
        events.append(("since", since))
        return ["clutch(a-b): Does X. Also Y."]

    def commit(repo, message, *, only):
        events.append(("commit", message, only))
        return "sha"

    def tag(repo, tag, message, sha):
        events.append(("tag", tag, sha))

    git = GitFake(status_porcelain=status, rev_parse=rev_parse, previous_release_tag=previous, merged_subjects=subjects, commit=commit, tag=tag)
    git.events = events
    return git


@pytest.mark.parametrize("previous", [None, "v0.3.0"])
def test_release_writes_before_commit(previous):
    git = make_git(previous)
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
    git = make_git(dirty=dirty, exists=exists)
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
