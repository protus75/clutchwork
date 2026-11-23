"""Intake lock timeouts retain pending work at the watcher poll boundary."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that Serve's watcher logs a commit-lock timeout during a ticket scan, keeps the pending ticket and in-flight work, and retries at the next poll, while ordinary errors and stop, kill or shutdown are raised without retry
# relates: [clutch/journal.py, clutch/lockfile.py, clutch/serve.py, clutch/tickets.py, tests/fakes.py, tests/unit/test_commit_lock.py]
# owner: engine
# verified: 333d8906
# hash: 64a18986ff76f1d01f100871925d4ac16d144313729790babd3be5494caa2655

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import serve, tickets
from clutch.journal import EventType
from clutch.lockfile import CommitLock, CommitLockTimeout
from clutch.tickets import parse_ticket
from tests.fakes import turn
from tests.unit.test_commit_lock import memory  # noqa: F401
from tests.unit.test_serve_dispatch_containment import rig  # noqa: F401


@pytest.mark.asyncio
async def test_scan_retries_owned_pending_ticket(rig, memory, monkeypatch):
    owner = rig.owner
    git = owner.checkout.git
    git._commit_lock = CommitLock(Path("/state"), clock=memory.clock, sleep=memory.sleep)
    pending = True
    commits = []
    git._overrides["status_porcelain"] = lambda *args: "?? tickets/alpha/ticket.md\n" if pending else ""
    git._overrides["_run"] = lambda *args: rig.text
    owner.checkout.fs.entries.return_value = ["alpha"]
    owner.stems = lambda: ["alpha"]
    owner.read = lambda stem: "ticket text"
    monkeypatch.setattr(tickets, "_intake_plan_stem", lambda *args: ("same", "same", SimpleNamespace(frontmatter=SimpleNamespace(source="human", state="confirmed"))))

    async def commit(path, message, *, only):
        nonlocal pending
        commits.append((message, only))
        pending = False
        return "sha"

    git._commit = commit
    sleep_gate = asyncio.Event()
    object.__setattr__(owner.checkout, "sleep", lambda _: sleep_gate.wait())
    changes = []

    async def watcher(source):
        async for stem in source:
            changes.append(stem)

    owner.core.watcher.run = watcher
    owner.core.watcher._waits = {}
    owner.core.scheduler._slot = asyncio.Lock()
    owner.control.poll = lambda: None
    owner.control.projection.stop_requested = False
    owner.control.projection.kill_requested = False
    entered = asyncio.Event()

    async def active_run(ticket):
        entered.set()
        await asyncio.Event().wait()

    rig.callback.side_effect = active_run
    other = asyncio.create_task(rig.dispatch(parse_ticket("aa", rig.text, rig.repo)))
    await entered.wait()
    task = asyncio.create_task(owner.watch())
    try:
        for _ in range(2000):
            if owner.log.event.call_count:
                break
            await turn()
        owner.log.event.assert_any_call("commit_lock_timeout", operation="scan", error=str(CommitLockTimeout(Path("/state/commit.lock"), {"pid": 729})))
        assert not task.done() and not other.done() and pending and commits == []
        memory.holder = None
        sleep_gate.set()
        for _ in range(2000):
            if changes:
                break
            await turn()
        for _ in range(100):
            await turn()
        assert changes == ["alpha"]
        assert commits == [("clutch(alpha): ticket", ["tickets/alpha/ticket.md"])]
        assert len([e for e in rig.journal.read() if e.type == EventType.SIGNAL and e.ticket == "alpha"]) == 1
        assert not task.done() and not other.done()
    finally:
        task.cancel()
        other.cancel()
        await asyncio.gather(task, other, return_exceptions=True)


@pytest.mark.asyncio
@pytest.mark.parametrize("ending", ["ordinary", "stop", "kill", "stopping"])
async def test_scan_does_not_retry_other_errors_or_shutdown(rig, memory, ending):
    owner = rig.owner
    owner.control.poll = lambda: None
    owner.stopping = ending == "stopping"
    owner.control.projection.stop_requested = ending == "stop"
    owner.control.projection.kill_requested = ending == "kill"
    error = ValueError("ordinary") if ending == "ordinary" else CommitLockTimeout(Path("/state/commit.lock"), None)
    owner.scan = AsyncMock(side_effect=error)
    object.__setattr__(owner.checkout, "sleep", AsyncMock(side_effect=AssertionError("unexpected retry")))

    async def watcher(source):
        async for _ in source:
            pass

    owner.core.watcher.run = watcher
    with pytest.raises(type(error)) as raised:
        await owner.watch()
    assert raised.value is error
    assert owner.scan.await_count == 1
    assert owner.log.event.call_count == 0
