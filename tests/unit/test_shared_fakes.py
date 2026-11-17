import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from clutch.journal import EventType
from tests.fakes import FakeClock, FakeExec, FakeFileSystem, FakeGit, FakeJournal, until


def test_fixtures(fake_clock, fake_exec, fake_fs, fake_journal, fake_git):
    for value, cls in ((fake_clock, FakeClock), (fake_exec, FakeExec), (fake_fs, FakeFileSystem), (fake_journal, FakeJournal), (fake_git, FakeGit)):
        assert isinstance(value, cls)


@pytest.mark.asyncio
async def test_until_pacing_and_no_sleep(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("sleep called")

    monkeypatch.setattr(asyncio, "sleep", forbidden)
    clock = FakeClock(datetime(2024, 2, 1, tzinfo=UTC))
    count = 0

    def predicate():
        nonlocal count
        count += 1
        return count > 45

    await until(predicate, clock, 2)
    assert clock() == datetime(2024, 2, 1, tzinfo=UTC) + timedelta(seconds=6)
    count = 0

    def hundred():
        nonlocal count
        count += 1
        return count > 100

    await until(hundred, clock, 2)
    assert count == 101


@pytest.mark.asyncio
async def test_until_timeout():
    with pytest.raises(AssertionError):
        await until(lambda: False, FakeClock(), 1, timeout=0.05)


def test_filesystem():
    fs = FakeFileSystem()
    root = Path("/fake")
    fs.write(root / "a", b"hello")
    fs.publish(root / "b", b"world!")
    assert fs.read_bytes(root / "a") == b"hello"
    assert fs.size(root / "b") == 6
    assert fs.entries(root) == ["a", "b"]
    with pytest.raises(FileExistsError):
        fs.publish(root / "a", b"new")
    fs.replace(root / "a", root / "c")
    assert fs.read_bytes(root / "c") == b"hello"
    fs.remove(root / "b")
    assert fs.entries(root) == ["c"]
    with pytest.raises(FileNotFoundError):
        fs.read_bytes(root / "a")


@pytest.mark.asyncio
async def test_exec_journal_git():
    exec_ = FakeExec((7, "out", "err"))
    result = await exec_.run(["git", "status"], cwd=Path("/repo"), env={}, timeout=3)
    assert result == (7, "out", "err")
    assert exec_.calls == [["git", "status"]]
    journal = FakeJournal(FakeClock(datetime(2024, 1, 2, tzinfo=UTC)))
    event = journal.append(EventType.EFFECT_INTENT, {"action": "run"}, ticket="one", key="key")
    assert journal.read() == [event]
    assert (event.type, event.body, event.ticket, event.key, event.ts) == (EventType.EFFECT_INTENT, {"action": "run"}, "one", "key", "2024-01-02T00:00:00+00:00")
    git = FakeGit({"status": "dirty"})
    assert git.status("repo", short=True) == "dirty"
    assert git.calls == [("status", ("repo",), {"short": True})]
