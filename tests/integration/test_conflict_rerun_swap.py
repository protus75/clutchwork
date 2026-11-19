"""Real rebase abort, reference lift, branch retirement and fresh admission."""

import asyncio

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
