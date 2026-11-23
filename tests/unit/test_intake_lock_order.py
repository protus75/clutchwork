# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that tickets.intake holds the main-write and commit locks in order through status, read, validation, stamp and commit, and that a competing writer waits until intake finishes
# relates: [clutch/git.py, clutch/tickets.py]
# owner: clutch/tickets.py
# verified: c3c5fa35
# hash: 77b9d14ea9584d6960804a380068fac27d9613a9d59575dd4780b83764e3ca78
import asyncio
from pathlib import Path
from types import SimpleNamespace

from clutch import tickets
from clutch.git import Git


def test_intake_holds_ordered_locks_through_edit_and_commit(monkeypatch):
    async def scenario():
        events = []
        lock = asyncio.Lock()
        lock._sleep = asyncio.sleep
        git = Git(None, env={}, timeout=1, commit_lock=lock)
        entered, release = asyncio.Event(), asyncio.Event()

        def check(step):
            assert git.main_write().locked() and lock.locked()
            events.append(step)

        async def status(repo):
            check("status")
            entered.set()
            await release.wait()
            return "?? tickets/one/ticket.md\n"

        async def pending(repo, git, entries):
            check("read")
            return {"one": True}, {"one": []}, []

        def plan(*args):
            check("validation")
            return "original", "stamped", SimpleNamespace(frontmatter=SimpleNamespace(source="human", state="confirmed"))

        async def commit(repo, message, *, only):
            check("commit")
            assert (message, only) == ("clutch(one): ticket", ["tickets/one/ticket.md"])
            return "sha"

        def write(path, data):
            check("stamp")
            assert data == b"stamped"

        git.status_porcelain = status
        git._commit = commit
        monkeypatch.setattr(tickets, "intake_pending", pending)
        monkeypatch.setattr(tickets, "_intake_plan_stem", plan)
        journal = SimpleNamespace(read=lambda: [], append=lambda *a, **kw: None)
        await lock.acquire()
        task = asyncio.create_task(tickets.intake(Path("/repo"), git, journal, SimpleNamespace(write=write), stems=None))
        await asyncio.sleep(0)
        assert git.main_write().locked() and not entered.is_set()
        lock.release()
        await entered.wait()
        competitor_entered = asyncio.Event()

        async def competitor():
            async with git.main_write():
                async with lock:
                    competitor_entered.set()

        other = asyncio.create_task(competitor())
        await asyncio.sleep(0)
        assert not competitor_entered.is_set()
        release.set()
        result = await task
        await other
        assert result.committed == ("one",)
        assert events == ["status", "read", "validation", "stamp", "commit"]
        assert competitor_entered.is_set()

    asyncio.run(scenario())
