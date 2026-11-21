"""Tests Rework ticket write locking."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that Rework's ticket-file writes are made under the commit lock through the shared Git.commit_edit owner.
# relates: [clutch/rework.py, clutch/git.py]
# owner: engine
# verified: 11213934
# hash: 8db7f934057d0d912f2dd2740be104555cf183233f33a958a3b9278deeee1b8d

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import daemon
from clutch.artifacts import Cost, StageResult
from clutch.git import Git, NothingToCommit
from clutch.rework import ReworkOrder


@pytest.mark.parametrize("case", ["success", "partial", "later"])
def test_callback_never_reenters_writer_lock(tmp_path, monkeypatch, case):
    files = {tmp_path / "tickets/first/ticket.md": b"old"}
    proposals = [("first", "new"), ("successor", "next")]
    ticket = SimpleNamespace(stem="item", stuck_minutes=1)
    order = ReworkOrder(action="split", tickets=[{"stem": stem, "ticket": text} for stem, text in proposals], stem="item", attempt=0, produced_by_spec_version=1, produced_at_sha="abc")
    result = StageResult(outcome="ok", artifact=order, cost=Cost(), findings=[])

    class Lock:
        held = False

        async def __aenter__(self):
            assert not self.held, "recursive writer lock"
            self.held = True

        async def __aexit__(self, *args):
            self.held = False

    lock = Lock()
    git = Git(None, env={}, timeout=None, commit_lock=lock)
    commits = []

    async def commit(root, message, *, only):
        assert lock.held and git.main_write().locked()
        commits.append(message)
        if case == "partial" and message.endswith(": rework"):
            raise RuntimeError("publication failed")
        if message.endswith("undo refused rework"):
            raise NothingToCommit([], 0, "", "")
        return "sha"

    async def read(root, *args):
        if args[0] == "ls-files":
            return "tickets/first/ticket.md"
        if args[1] == "HEAD:tickets/item/ticket.md" and len(commits) == 0:
            return "old"
        return files[tmp_path / args[1].removeprefix("HEAD:")].decode()

    def write(path, data):
        assert lock.held and git.main_write().locked()
        files[path] = data

    def remove(path):
        assert lock.held and git.main_write().locked()
        del files[path]

    async def effect(action, **kwargs):
        return await action()

    async def supersedes(*args):
        if case == "later":
            files[tmp_path / "tickets/first/ticket.md"] = b"later"
            return [SimpleNamespace()]
        return []

    monkeypatch.setattr(Path, "is_file", lambda path: path in files)
    monkeypatch.setattr(git, "_commit", commit)
    monkeypatch.setattr(git, "_run", read)
    monkeypatch.setattr(daemon, "parse_ticket", lambda *args: ticket)
    monkeypatch.setattr(daemon.runner, "capability", lambda *args: ("low", "low"))
    monkeypatch.setattr(daemon, "rework", AsyncMock(return_value=result))
    monkeypatch.setattr(daemon, "record_supersedes", supersedes)
    ctx = SimpleNamespace(
        repo=tmp_path,
        worktree=lambda _: tmp_path,
        git=git,
        fs=SimpleNamespace(write=write, remove=remove, read_bytes=files.__getitem__),
        driver=SimpleNamespace(journal=SimpleNamespace(read=lambda: []), effects=SimpleNamespace(run=effect), redactor=SimpleNamespace(scrub=str)),
    )
    monkeypatch.setattr(Path, "exists", lambda path: path == tmp_path)
    outcome = asyncio.run(daemon.apply_rework(ctx, ticket, [], attempt=0))
    assert outcome.outcome == ("ok" if case == "success" else "gate_failed")
    assert files == (
        {tmp_path / "tickets/first/ticket.md": b"new", tmp_path / "tickets/successor/ticket.md": b"next"}
        if case == "success"
        else {tmp_path / "tickets/first/ticket.md": b"later" if case == "later" else b"old"}
    )
    assert len(commits) == (1 if case == "success" else 2)
