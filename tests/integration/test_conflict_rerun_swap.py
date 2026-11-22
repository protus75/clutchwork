"""Real rebase abort, reference lift, branch retirement and fresh admission."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that a declined merge conflict aborts the rebase, lifts the prior diff without conflicted paths, retires the branch and worktree, records a conflict rerun without spending attempts, and re-offers the ticket from current main
# relates: [clutch/caps.py, clutch/daemon.py, clutch/drain.py, clutch/journal.py, clutch/llm.py, clutch/mergequeue.py, tests/integration/test_mergequeue.py]
# owner: engine
# verified: d32c32ad
# hash: 709e1f81c9171f5b3f0f474d2415faa9df284c175e44e87696cde7957bbd7845

import asyncio

import pytest

from clutch import caps, drain
from clutch.daemon import TicketWriter
from clutch.journal import EventType
from clutch.llm import FakeLLM
from clutch.mergequeue import MergeQueue
from tests.integration.test_mergequeue import (
    commit,
    conflict,
    ctx,  # noqa: F401
)

pytestmark = pytest.mark.disk_io_skip


def test_discard_reoffers_from_current_main(ctx):
    async def scenario():
        ticket, conflicted = await conflict(ctx)
        ctx.config.merge.strategies = []
        ctx.driver.llm = FakeLLM(['{"verdict":"decline","reason":"incompatible","files":{}}'])
        queue = MergeQueue(ctx, escalate=lambda _: None)
        writer = TicketWriter(ctx, queue)
        queue.offer(ticket, attempt=7)
        [result] = await queue.process()
        # Forgetting abort leaves an unmerged index and a detached rebase head.
        assert await ctx.git.conflicted_paths(ctx.worktree(ticket.stem)) == []
        assert await ctx.git.rev_parse(ctx.worktree(ticket.stem), "HEAD") == await ctx.git.rev_parse(ctx.repo, ticket.stem)
        await writer.consume_result(ticket, result, attempt=7)
        # Keeping the branch/worktree or lifting all paths fails these distinct checks.
        assert not ctx.worktree(ticket.stem).exists()
        assert (await ctx.git._call(ctx.repo, "rev-parse", "--verify", ticket.stem))[1] != 0
        prior = (ctx.repo / f"tickets/{ticket.stem}/attempts/7/prior.diff").read_text()
        assert f"diff --git a/{conflicted}" not in prior
        assert "diff --git a/clutch/thing.py" in prior and "+ok work" in prior
        history = ctx.driver.journal.read()
        assert [e.body for e in history if e.body.get("signal") == "merge_conflict_rerun"] == [{"signal": "merge_conflict_rerun", "attempt": 7}]
        assert caps.failed_attempts(history, ticket.stem) == 0
        assert drain.reofferable(history, ticket.stem, ctx.config.caps)
        drain.record_reoffer(ctx.driver.journal, history, ticket.stem, "ticket-sha")
        assert not any(e.type == EventType.CAP_CONSUMED for e in ctx.driver.journal.read())
        # A fresh branch starts with main's conflict version and no applied discarded edit.
        await ctx.git.worktree_add(ctx.repo, ctx.worktree(ticket.stem), ticket.stem, "main")
        assert (ctx.worktree(ticket.stem) / conflicted).read_text() == "base\nmain\n"
        assert (ctx.worktree(ticket.stem) / "clutch/thing.py").read_text() == "ok base\n"
        ctx.fs.write(ctx.worktree(ticket.stem) / "clutch/thing.py", b"ok re-derived\n")
        await commit(ctx, ctx.worktree(ticket.stem), ["clutch/thing.py"])
        queue.offer(ticket, attempt=8)
        assert queue.pending[ticket.stem] == (ticket, 8)

    asyncio.run(scenario())
