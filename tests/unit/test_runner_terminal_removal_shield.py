"""Cancellation waits for the already-satisfied worktree removal."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that cancelling runner.drive waits for the already-satisfied worktree removal to finish, after the single terminal transition is journaled.
# relates: [clutch/journal.py, clutch/runner.py]
# owner: engine
# verified: 73ec5da9
# hash: 4f361567cb216112299f843c6b5f5c4bebdc6922f95ac98c4c3e81e2a704f680

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import runner
from clutch.journal import EventType
from tests.git_fake import GitFake


@pytest.mark.asyncio
async def test_terminal_removal_finishes_before_cancellation(monkeypatch):
    events = []
    paths = set()

    class Worktree:
        def exists(self):
            return self in paths

    path = Worktree()
    paths.add(path)
    started = asyncio.Event()
    release = asyncio.Event()
    completed = []
    events_at_start = []

    async def worktree_remove(repo, worktree):
        events_at_start.extend(events)
        started.set()
        await release.wait()
        paths.remove(worktree)
        completed.append((repo, worktree))

    class Journal:
        def append(self, kind, body, *, ticket):
            events.append((kind, body, ticket))

    ctx = SimpleNamespace(
        repo=Path("/fake/repo"),
        git=GitFake(worktree_remove=worktree_remove),
        worktree=lambda stem: path,
        driver=SimpleNamespace(journal=Journal()),
        boundary=SimpleNamespace(run=object(), next_stage=None),
    )
    ticket = SimpleNamespace(stem="work")
    result = SimpleNamespace(outcome="already_satisfied")
    monkeypatch.setattr(runner, "run_stages", AsyncMock(return_value=SimpleNamespace(last=("implement", result), ticket_sha="sha")))
    monkeypatch.setattr(runner, "ticket_change_findings", AsyncMock(return_value=[]))

    task = asyncio.create_task(runner.drive(ctx, ticket))
    await started.wait()
    task.cancel()
    await asyncio.sleep(0)
    # Wrong: propagate cancellation immediately while cleanup remains unfinished.
    assert not task.done()
    release.set()
    # Wrong: swallow cancellation and return success.
    with pytest.raises(asyncio.CancelledError):
        await task
    # Wrong: report cancellation before the removal actually finishes or removes the path.
    assert completed == [(ctx.repo, path)] and path not in paths
    # Wrong: start removal before recording the terminal transition.
    assert events_at_start == [(EventType.STATE_TRANSITION, {"to": "already_satisfied", "stage": "implement", "reason": "already_satisfied"}, "work")]
    # Wrong: omit or duplicate the terminal transition.
    assert events == [(EventType.STATE_TRANSITION, {"to": "already_satisfied", "stage": "implement", "reason": "already_satisfied"}, "work")]
