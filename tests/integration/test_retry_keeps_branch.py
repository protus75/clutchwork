# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that prepare_worktree reattaches and rebases the earlier branch when keeping it, and starts a fresh branch from main when the rebase is refused or the branch is not kept
# relates: [clutch/git.py, clutch/stages.py, tests/fakes.py]
# owner: clutch/stages.py
# verified: 10f08d74
# hash: 2aff47440fba5310f1819959b3f205c6b04472a687c2ab32bc9ede40db31effa
import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from clutch.git import RebaseRefused
from clutch.stages import prepare_worktree
from tests.fakes import FakeFileSystem
from tests.git_fake import GitFake


@pytest.mark.parametrize(
    ("keep", "fail", "expected"),
    [
        (True, False, ["worktree_remove", "rev_parse", "worktree_attach", "rebase"]),
        (True, True, ["worktree_remove", "rev_parse", "worktree_attach", "rebase", "worktree_remove", "branch_delete", "worktree_add"]),
        (False, False, ["worktree_remove", "rev_parse", "branch_delete", "worktree_add"]),
    ],
)
def test_prepare(monkeypatch, keep, fail, expected):
    repo, path = Path("/repo"), Path("/work/feature")
    monkeypatch.setattr(Path, "exists", lambda self: self == path)
    git = GitFake(rebase=RebaseRefused([], 1, "", "conflict") if fail else None)
    ctx = SimpleNamespace(repo=repo, git=git, fs=FakeFileSystem(), worktree=lambda stem: path)
    assert asyncio.run(prepare_worktree(ctx, "feature", keep=keep)) == path
    assert [call[0] for call in git.calls] == expected
    if keep:
        assert ("worktree_attach", (repo, path, "feature"), {}) in git.calls
        assert ("rebase", (path, "main"), {}) in git.calls
    if not keep or fail:
        assert ("branch_delete", (repo, "feature"), {}) in git.calls
        assert ("worktree_add", (repo, path, "feature", "main"), {}) in git.calls
