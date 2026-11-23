# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that intake commits each stem with its own evidence paths, releases the commit lock between stems so a polling writer can get in, and refuses stray staged paths, symlinks and other stems' evidence
# relates: [clutch/lockfile.py, clutch/tickets.py, tests/git_fake.py, tests/unit/test_commit_lock.py]
# owner: engine
# verified: c3c5fa35
# hash: ec2ad0a202d183cda218a3457d295fa068ea0ef499ac046b170441ed19b6c345
import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from clutch import tickets
from clutch.lockfile import CommitLock
from tests.git_fake import GitFake
from tests.unit.test_commit_lock import memory  # noqa: F401


def test_inventory_and_polling_writer(memory, monkeypatch):
    memory.holder = None
    repo = Path("/repo")
    regular = {"tickets/alpha/evidence/a", "tickets/beta/evidence/b", "tickets/other/evidence/x", "tickets/alpha/evidence/ignored"}
    monkeypatch.setattr(Path, "is_file", lambda path: str(path.relative_to(repo)) in regular or str(path).endswith("/link"))
    monkeypatch.setattr(Path, "is_symlink", lambda path: str(path).endswith("/link"))
    monkeypatch.setattr(tickets, "_intake_plan_stem", lambda *args: ("same", "same", SimpleNamespace(frontmatter=SimpleNamespace(source="human", state="confirmed"))))
    inventory = ["tickets/beta/evidence/b", "tickets/alpha/evidence/a", "tickets/alpha/evidence/link", "tickets/other/evidence/x", "tickets/alpha-extra/evidence/wrong"]
    entries = "?? tickets/beta/ticket.md\n?? tickets/alpha/ticket.md\nA  tickets/alpha/evidence/a\n"
    calls, events, recorded = [], [], []

    def run(path, *args):
        calls.append(args)
        return "\0".join(inventory)

    async def scenario():
        polled = asyncio.Event()
        original_sleep = memory.sleep

        async def sleep(seconds):
            if memory.holder is not None:
                polled.set()
            await original_sleep(seconds)

        lock = CommitLock(Path("/state"), clock=memory.clock, sleep=sleep)
        contender_lock = CommitLock(Path("/state"), clock=memory.clock, sleep=sleep)
        git = GitFake(status_porcelain=entries, _run=run)
        git._commit_lock = lock

        async def contender():
            async with contender_lock:
                events.append("contender")

        async def commit(path, message, *, only):
            events.append((message, only))
            if message == "clutch(alpha): ticket":
                task = asyncio.create_task(contender())
                await polled.wait()
                git.contender = task
            return "sha"

        git._commit = commit
        journal = SimpleNamespace(read=lambda: [], append=lambda *args, **kwargs: recorded.append(kwargs["ticket"]))
        result = await tickets.intake(repo, git, journal, SimpleNamespace(), stems=None)
        await git.contender
        assert result.committed == ("alpha", "beta")
        assert recorded == ["alpha", "beta"]
        assert events == [
            ("clutch(alpha): ticket", ["tickets/alpha/ticket.md", "tickets/alpha/evidence/a"]),
            "contender",
            ("clutch(beta): ticket", ["tickets/beta/ticket.md", "tickets/beta/evidence/b"]),
        ]
        assert calls == [("ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", "tickets/")]

        for staged in ("outside.py", "tickets/alpha/evidence/link", "tickets/other/evidence/x"):
            git._overrides["status_porcelain"] = entries + f"A  {staged}\n"
            events.clear()
            with pytest.raises(tickets.IntakeRefused):
                await tickets.intake(repo, git, journal, SimpleNamespace(), stems=None)
            assert events == []

    asyncio.run(scenario())
