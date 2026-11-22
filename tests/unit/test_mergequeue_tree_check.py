"""Tree validation accepts only ticket-plane differences."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Merge tree validation accepts ticket-plane-only differences, and pauses the queue with a tree-mismatch event on other diffs or a git error
# relates: [clutch/git.py, clutch/merge.py, clutch/mergequeue.py]
# owner: engine
# verified: 452057e3
# hash: 1953ccb1df31aaabba3431e44bab0f4e5723a08a8631187f1d354ac2b4b9b5a1

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import merge
from clutch.git import GitError
from clutch.mergequeue import TREE_MISMATCH, MergeQueue, TreeMismatch
from tests.git_fake import GitFake


@pytest.mark.parametrize("paths", ["tickets/x/run.md", "docs/roadmap.md", "tickets/x/run.md\ndocs/roadmap.md"])
def test_ticket_plane_diff_is_accepted(monkeypatch, paths):
    result, queue, events, git = exercise(monkeypatch, paths)
    assert result.outcome == "ok"
    assert not queue.paused and events == []
    assert [call for call in git.calls if call[0] == "_run"] == [("_run", ("repo", "diff", "--name-only", "checked", "main-tree"), {})]


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
    git = GitFake(rev_parse="main-tree", _run=paths)
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
