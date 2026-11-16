import asyncio

import pytest

from clutch import merge, stages
from clutch.artifacts import Cost, StageResult
from clutch.journal import EventType
from clutch.mergequeue import MergeQueue
from tests.integration.test_mergequeue import commit, ctx, ready  # noqa: F401


@pytest.mark.parametrize("inline", [True, False])
def test_admission_gathers_safety_once(ctx, monkeypatch, inline):
    async def scenario():
        ticket = await ready(ctx)
        ctx.fs.write(ctx.repo / "clutch/other.py", b"main changed\n")
        await commit(ctx, ctx.repo, ["clutch/other.py"])
        original = stages.gather_safety_evidence
        calls = []

        async def count(*args, **kwargs):
            calls.append(1)
            return await original(*args, **kwargs)

        monkeypatch.setattr(stages, "gather_safety_evidence", count)
        result = await merge.merge(ctx, ticket, attempt=0) if inline else await MergeQueue(ctx, escalate=lambda _: None)._admit(ticket, 0)
        assert result.outcome == "ok"
        assert len(calls) == 1

    asyncio.run(scenario())


def test_inline_delegates_to_queue(ctx, monkeypatch):
    sentinel = StageResult(outcome="ok", artifact=None, findings=[], cost=Cost(seconds=3))

    async def admit(self, ticket, attempt, **kwargs):
        return sentinel

    monkeypatch.setattr(MergeQueue, "_admit", admit)
    assert asyncio.run(merge.merge(ctx, object(), attempt=4)) is sentinel


def test_served_review_rejects_malformed_record(ctx):
    async def scenario():
        ticket = await ready(ctx)
        path = f"tickets/{ticket.stem}/review.md"
        ctx.fs.write(ctx.repo / path, b"```json\nnot json\n```\n")
        await commit(ctx, ctx.repo, [path])
        sha = await ctx.git.rev_parse(ctx.repo, "main")
        ctx.driver.journal.append(EventType.EFFECT_COMPLETION, {"result": {"kind": "review", "paths": [path], "commit": sha}}, ticket=ticket.stem, key=f"ticket-plane/{ticket.stem}/0/review")
        with pytest.raises(ValueError):
            await stages.served_review(ctx, ticket.stem, 0, "reviewed")

    asyncio.run(scenario())


def test_served_review_without_lift_is_unattested(ctx):
    assert asyncio.run(stages.served_review(ctx, "missing", 0, "reviewed")) == (None, None)
