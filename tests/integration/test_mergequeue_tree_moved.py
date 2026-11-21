"""Real tree validation after main moves between check and squash."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose:
# relates: [clutch/journal.py, clutch/merge.py, clutch/mergequeue.py, tests/integration/test_mergequeue.py]
# owner: engine
# verified: fc0ba349
# hash: a87488fea5e85a46dbd86ec8f6bd9160382452f38d8348bc8a013326694f8f63

import asyncio

import pytest

from clutch import merge
from clutch.journal import EventType
from clutch.mergequeue import TREE_MISMATCH, MergeQueue, TreeMismatch
from tests.integration.test_mergequeue import commit, ctx, ready  # noqa: F401


@pytest.mark.parametrize("path, mismatch", [("tickets/other/run.md", False), ("docs/roadmap.md", False), ("clutch/other.py", True)])
def test_main_moves_after_check(ctx, path, mismatch):
    async def scenario():
        ticket = await ready(ctx)
        checked = await ctx.git.rev_parse(ctx.worktree(ticket.stem), "HEAD^{tree}")
        reviewed = await ctx.git.rev_parse(ctx.repo, ticket.stem)
        ctx.fs.write(ctx.repo / path, b"later main change\n")
        await commit(ctx, ctx.repo, [path], "main moves after check")
        queue = MergeQueue(ctx, escalate=lambda event: None)
        call = queue._finish(ticket, 0, reviewed, checked, ctx.driver.clock())
        if mismatch:
            with pytest.raises(TreeMismatch):
                await call
        else:
            result = await call
            assert result.outcome == "ok"
        signals = [event for event in ctx.driver.journal.read() if event.type == EventType.SIGNAL and event.body.get("kind") == TREE_MISMATCH]
        assert queue.paused is mismatch
        assert len(signals) == int(mismatch)
        assert any(event.type == EventType.STATE_TRANSITION and event.body.get("to") == "merged" for event in ctx.driver.journal.read())

    asyncio.run(scenario())
