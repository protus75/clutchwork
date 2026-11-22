# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests prepare_worktree reattaches and rebases the prior branch when keeping it, and falls back to a fresh branch from main on rebase refusal or no keep
# relates: [clutch/git.py, clutch/stages.py, tests/fakes.py]
# owner: clutch/stages.py
# verified: 52843322
# hash: 05f73488408c29e4a56060ddbaf12715b39095f9ce3f256b23827ed18172c89e
import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from clutch.git import RebaseRefused
from clutch.stages import prepare_worktree
from tests.fakes import FakeFileSystem


class Git:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    async def worktree_remove(self, *args):
        self.calls.append(("remove", *args))

    async def worktree_prune(self, *args):
        self.calls.append(("prune", *args))

    async def rev_parse(self, *args):
        self.calls.append(("rev_parse", *args))

    async def branch_delete(self, *args):
        self.calls.append(("delete", *args))

    async def worktree_attach(self, *args):
        self.calls.append(("attach", *args))

    async def rebase(self, *args):
        self.calls.append(("rebase", *args))
        if self.fail:
            raise RebaseRefused([], 1, "", "conflict")

    async def worktree_add(self, *args):
        self.calls.append(("add", *args))


@pytest.mark.parametrize(
    ("keep", "fail", "expected"),
    [
        (True, False, ["remove", "rev_parse", "attach", "rebase"]),
        (True, True, ["remove", "rev_parse", "attach", "rebase", "remove", "delete", "add"]),
        (False, False, ["remove", "rev_parse", "delete", "add"]),
    ],
)
def test_prepare(monkeypatch, keep, fail, expected):
    repo, path = Path("/repo"), Path("/work/feature")
    monkeypatch.setattr(Path, "exists", lambda self: self == path)
    git = Git(fail)
    ctx = SimpleNamespace(repo=repo, git=git, fs=FakeFileSystem(), worktree=lambda stem: path)
    assert asyncio.run(prepare_worktree(ctx, "feature", keep=keep)) == path
    assert [call[0] for call in git.calls] == expected
    if keep:
        assert ("attach", repo, path, "feature") in git.calls
        assert ("rebase", path, "main") in git.calls
    if not keep or fail:
        assert ("delete", repo, "feature") in git.calls
        assert ("add", repo, path, "feature", "main") in git.calls
