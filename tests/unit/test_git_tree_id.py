# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test git tree id
# relates: [clutch/git.py]
# owner: clutch/git.py
# verified: 0a308920
# hash: 984a4affc991f96ede21a02fa9c0980a8fd923c10808c5d640c2983c850682ec
import asyncio
from pathlib import Path

import pytest

from clutch.git import Git, GitError


class FakeExec:
    def __init__(self, *results):
        self.results = list(results)
        self.calls = []

    async def run(self, argv, *, cwd, env, timeout):
        self.calls.append((argv, cwd, dict(env), timeout))
        return self.results.pop(0)


def test_tree_id_argv_env_and_result():
    process = FakeExec((0, "added\n", ""), (0, "abc123\n", ""))
    git = Git(process, env={"PATH": "/bin", "GIT_INDEX_FILE": "old"}, timeout=7, commit_lock=None)
    assert asyncio.run(git.tree_id(Path("/repo"), Path("/state/x.index"))) == "abc123"
    env = {"PATH": "/bin", "GIT_INDEX_FILE": "/state/x.index"}
    assert process.calls == [
        (["git", "-C", "/repo", "add", "-A"], Path("/repo"), env, 7),
        (["git", "-C", "/repo", "write-tree"], Path("/repo"), env, 7),
    ]


def test_tree_id_failure_raises():
    process = FakeExec((1, "output", "failure"))
    git = Git(process, env={}, timeout=7, commit_lock=None)
    with pytest.raises(GitError) as error:
        asyncio.run(git.tree_id(Path("/repo"), Path("/state/x.index")))
    assert error.value.argv == ["git", "-C", "/repo", "add", "-A"]
    assert len(process.calls) == 1
    process = FakeExec((0, "", ""), (1, "", "failure"))
    git = Git(process, env={}, timeout=7, commit_lock=None)
    with pytest.raises(GitError) as error:
        asyncio.run(git.tree_id(Path("/repo"), Path("/state/x.index")))
    assert error.value.argv == ["git", "-C", "/repo", "write-tree"]


def test_tree_changes_argv_and_lines():
    process = FakeExec((0, "a.py\nb/c.py\n", ""), (0, "", ""))
    git = Git(process, env={"PATH": "/bin"}, timeout=7, commit_lock=None)
    assert asyncio.run(git.tree_changes(Path("/repo"), "t1", "t2")) == ["a.py", "b/c.py"]
    assert process.calls[0] == (["git", "-C", "/repo", "diff", "--name-only", "t1", "t2"], Path("/repo"), {"PATH": "/bin"}, 7)
    assert asyncio.run(git.tree_changes(Path("/repo"), "t1", "t1")) == []
    for before, after in (("-x", "t2"), ("t1", "-x")):
        with pytest.raises(ValueError):
            asyncio.run(git.tree_changes(Path("/repo"), before, after))
    assert len(process.calls) == 2
