import asyncio
import os

from clutch.git import Git
from clutch.seams import SubprocessExec
from tests.integration.test_git import commit_lock


def setup_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    git = Git(SubprocessExec(), env=env, timeout=30.0, commit_lock=commit_lock(tmp_path / ".clutch/state"))
    return repo, git


async def prepare(repo, git):
    await git.init(repo, branch="main")
    (repo / "tracked.txt").write_text("old\n")
    await git.add(repo, ["tracked.txt"])
    await git.commit(repo, "base")
    (repo / "tracked.txt").write_text("new\n")
    (repo / "untracked.txt").write_text("untracked\n")


def test_tree_id_captures_worktree_without_touching_index(tmp_path):
    repo, git = setup_repo(tmp_path)

    async def scenario():
        await prepare(repo, git)
        index = (repo / ".git/index").read_bytes()
        status = await git.status_porcelain(repo)
        head = await git.rev_parse(repo, "HEAD")
        reflog = (repo / ".git/logs/refs/heads/main").read_bytes()
        tree = await git.tree_id(repo, tmp_path / "snapshot.index")
        listing = await git._run(repo, "ls-tree", "-r", tree)
        tracked_blob = (await git._run(repo, "hash-object", "tracked.txt")).strip()
        assert f"{tracked_blob}\ttracked.txt" in listing
        assert "\tuntracked.txt" in listing
        assert (repo / ".git/index").read_bytes() == index
        assert await git.status_porcelain(repo) == status
        assert await git.rev_parse(repo, "HEAD") == head
        assert (repo / ".git/logs/refs/heads/main").read_bytes() == reflog

    asyncio.run(scenario())


def test_tree_changes_lists_paths_between_trees(tmp_path):
    repo, git = setup_repo(tmp_path)

    async def scenario():
        await prepare(repo, git)
        before = await git.rev_parse(repo, "HEAD^{tree}")
        after = await git.tree_id(repo, tmp_path / "snapshot.index")
        assert await git.tree_changes(repo, before, after) == ["tracked.txt", "untracked.txt"]
        assert await git.tree_changes(repo, after, after) == []

    asyncio.run(scenario())
