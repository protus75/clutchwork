# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Test atomic ticket edits and commits under both locks.
# relates: [clutch/git.py]
# owner: clutch/git.py
# verified: cd8a8d84
# hash: d3f34656496f3b3d59087d7d9b8543a7e61d832c87908271563ae05f9e2be030
import asyncio
from pathlib import Path

import pytest

from clutch.git import Git


class Exec:
    def __init__(self, git, events):
        self.git, self.events = git, events

    async def run(self, argv, **kwargs):
        assert self.git.main_write().locked() and self.git._commit_lock.locked()
        self.events.append(argv[3:])
        return (1 if argv[3] == "diff" else 0), "new-sha\n", ""


def test_edit_commit_and_competitor():
    async def scenario():
        events = []
        lock = asyncio.Lock()
        git = Git(None, env={}, timeout=1, commit_lock=lock)
        git._exec = Exec(git, events)
        entered, release = asyncio.Event(), asyncio.Event()

        async def edit():
            assert git.main_write().locked() and lock.locked()
            events.append("edit")
            entered.set()
            await release.wait()

        async def other():
            await git.commit_edit(Path("/repo"), "other", only=["b"], edit=lambda: record())

        async def record():
            events.append("other edit")

        await lock.acquire()
        first = asyncio.create_task(git.commit_edit(Path("/repo"), "message", only=["a", "nested/b"], edit=edit))
        await asyncio.sleep(0)
        assert git.main_write().locked() and not entered.is_set()
        lock.release()
        await entered.wait()
        second = asyncio.create_task(other())
        await asyncio.sleep(0)
        assert events == ["edit"]
        release.set()
        assert await first == "new-sha"
        await second
        assert events == [
            "edit",
            ["update-index", "--add", "--remove", "--", "a", "nested/b"],
            ["diff", "--cached", "--quiet", "HEAD", "--", "a", "nested/b"],
            ["commit", "-m", "message", "--only", "--", "a", "nested/b"],
            ["rev-parse", "--verify", "HEAD"],
            "other edit",
            ["update-index", "--add", "--remove", "--", "b"],
            ["diff", "--cached", "--quiet", "HEAD", "--", "b"],
            ["commit", "-m", "other", "--only", "--", "b"],
            ["rev-parse", "--verify", "HEAD"],
        ]
        assert not git.main_write().locked() and not lock.locked()

    asyncio.run(scenario())


@pytest.mark.parametrize("cancel", [False, True])
def test_failure_releases_locks(cancel):
    async def scenario():
        lock = asyncio.Lock()
        git = Git(None, env={}, timeout=1, commit_lock=lock)
        entered = asyncio.Event()

        async def edit():
            entered.set()
            if cancel:
                await asyncio.Event().wait()
            raise RuntimeError("edit failed")

        task = asyncio.create_task(git.commit_edit(Path("/repo"), "x", only=["a"], edit=edit))
        await entered.wait()
        if cancel:
            task.cancel()
        with pytest.raises(asyncio.CancelledError if cancel else RuntimeError):
            await task
        assert not git.main_write().locked() and not lock.locked()
        with pytest.raises(ValueError):
            await git.commit_edit(Path("/repo"), "x", only=[], edit=edit)

    asyncio.run(scenario())
