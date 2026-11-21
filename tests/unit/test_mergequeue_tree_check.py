"""Tree validation accepts only ticket-plane differences."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose:
# relates: [clutch/git.py, clutch/merge.py, clutch/mergequeue.py]
# owner: engine
# verified: fc0ba349
# hash: 5177ac49196f5365782abe966e23fb4ceb3acc3db0976456bc91eaf7a2c02da1

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import merge
from clutch.git import GitError
from clutch.mergequeue import TREE_MISMATCH, MergeQueue, TreeMismatch


@pytest.mark.parametrize("paths", ["tickets/x/run.md", "docs/roadmap.md", "tickets/x/run.md\ndocs/roadmap.md"])
def test_ticket_plane_diff_is_accepted(monkeypatch, paths):
    result, queue, events, git = exercise(monkeypatch, paths)
    assert result.outcome == "ok"
    assert not queue.paused and events == []
    git._run.assert_awaited_once_with("repo", "diff", "--name-only", "checked", "main-tree")


@pytest.mark.parametrize("paths", ["clutch/a.py", GitError(["git", "diff"], 1, "", "bad tree")])
def test_other_diff_or_git_error_holds(monkeypatch, paths):
    result, queue, events, _ = exercise(monkeypatch, paths, mismatch=True)
    assert isinstance(result, TreeMismatch)
    assert queue.paused
    assert len(events) == 1
    assert events[0]["kind"] == TREE_MISMATCH
    assert events[0]["checked_tree"] == "checked" and events[0]["main_tree"] == "main-tree"


def exercise(monkeypatch, paths, mismatch=False):
    now = datetime(2026, 1, 1, tzinfo=UTC)
    events = []
    journal = SimpleNamespace(append=lambda kind, body, **kw: events.append(body))
    driver = SimpleNamespace(effects=SimpleNamespace(recorded=lambda key: []), journal=journal, clock=lambda: now)
    git = SimpleNamespace(rev_parse=AsyncMock(return_value="main-tree"), _run=AsyncMock())
    if isinstance(paths, Exception):
        git._run.side_effect = paths
    else:
        git._run.return_value = paths
    ctx = SimpleNamespace(driver=driver, git=git, repo="repo")
    monkeypatch.setattr(merge, "write_squash", AsyncMock(return_value=SimpleNamespace(commit="squash")))
    monkeypatch.setattr(merge, "retire", AsyncMock())
    queue = MergeQueue(ctx, escalate=lambda event: None)
    call = queue._finish(SimpleNamespace(stem="x"), 0, "reviewed", "checked", now)
    if mismatch:
        with pytest.raises(TreeMismatch) as exc:
            asyncio.run(call)
        result = exc.value
    else:
        result = asyncio.run(call)
    return result, queue, events, git
