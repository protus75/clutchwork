"""Release bumps keep a committed portable plugin in sync."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests checking that a release bump writes the portable plugin bundle again before it commits, refuses when the bundle files are dirty, and still releases normally when the bundle is missing or invalid.
# relates: [clutch/antigravity.py, clutch/git.py, clutch/release.py, clutch/runner.py, tests/git_fake.py]
# owner: engine
# verified: 0626363d
# hash: 34ec7c1447bbe2a0997036ffe1a933ea8dc067949efca5fe14a311f42607975a

import asyncio
import json
from pathlib import Path

import pytest

from clutch.antigravity import portable_bundle_files
from clutch.git import GitError
from clutch.release import release
from clutch.runner import Refusal
from tests.git_fake import GitFake

REPO = Path("/repo")
BASE = ["pyproject.toml", "uv.lock", "CHANGELOG.md"]
LOGO = b"distinct logo bytes"


class FS:
    def __init__(self, files):
        self.files = files
        self.writes = []

    def read_bytes(self, path):
        try:
            return self.files[path.relative_to(REPO).as_posix()]
        except KeyError:
            raise FileNotFoundError(path) from None

    def write(self, path, data):
        self.writes.append((path.relative_to(REPO).as_posix(), data))


class Process:
    def __init__(self):
        self.calls = []

    async def run(self, argv, **kwargs):
        self.calls.append(argv)
        return 0, "0.8.0", ""


def invoke(files, dirty=""):
    fs = FS(files)
    process = Process()
    git = GitFake(status_porcelain=dirty, rev_parse=GitError([], 1, "", "missing"), commit="release-sha")
    return fs, process, git


def run(fs, process, git):
    return asyncio.run(release(REPO, git, process, fs, {}, "minor", "2026-11-25"))


def test_bundle_regenerated_before_commit():
    fs, process, git = invoke({"plugin.json": b'{"name":"clutchwork", "version":"0.7.0"}', "clutch/assets/logo.png": LOGO})
    writes_at_commit = []

    def commit(repo, message, *, only):
        writes_at_commit.extend(fs.writes)
        return "release-sha"

    git._overrides["commit"] = commit
    assert run(fs, process, git) == ("0.8.0", "release-sha")
    expected = portable_bundle_files(version_str="0.8.0", logo_bytes=LOGO)
    assert dict(fs.writes)["CHANGELOG.md"].startswith(b"# Changelog")
    assert dict(fs.writes[1:]) == expected
    assert json.loads(dict(fs.writes)["plugin.json"])["version"] == "0.8.0"
    assert writes_at_commit == fs.writes
    paths = BASE + sorted(expected)
    assert git.calls[0] == ("status_porcelain", (REPO, "--", *paths), {})
    assert next(call for call in git.calls if call[0] == "commit") == ("commit", (REPO, "release: 0.8.0"), {"only": paths})
    assert git.calls[-1] == ("tag", (REPO, "v0.8.0", "release: 0.8.0", "release-sha"), {})


def test_dirty_bundle_refuses_before_writes_or_uv():
    fs, process, git = invoke({"plugin.json": b'{"name":"clutchwork"}', "clutch/assets/logo.png": LOGO}, " M skills/clutch-drain-loop/SKILL.md")
    with pytest.raises(Refusal, match="skills/clutch-drain-loop/SKILL.md"):
        run(fs, process, git)
    assert git.calls == [("status_porcelain", (REPO, "--", *BASE, *sorted(portable_bundle_files(version_str="", logo_bytes=LOGO))), {})]
    assert process.calls == []
    assert fs.writes == []


@pytest.mark.parametrize(
    "files",
    [
        {},
        {"plugin.json": b"not json", "clutch/assets/logo.png": LOGO},
        {"plugin.json": b"[]", "clutch/assets/logo.png": LOGO},
        {"plugin.json": b'{"name":"other"}', "clutch/assets/logo.png": LOGO},
        {"plugin.json": b'{"name":"clutchwork"}'},
    ],
)
def test_absent_bundle_preserves_release(files):
    fs, process, git = invoke(files)
    assert run(fs, process, git) == ("0.8.0", "release-sha")
    assert git.calls[0] == ("status_porcelain", (REPO, "--", *BASE), {})
    assert next(call for call in git.calls if call[0] == "commit")[2]["only"] == BASE
    assert [name for name, _ in fs.writes] == ["CHANGELOG.md"]
