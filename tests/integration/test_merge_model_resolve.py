"""Real rebase/index and serve admission with scripted model replies."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests model-driven merge conflict resolution through a real rebase and index, and serve admission with scripted model replies
# relates: [clutch/artifacts.py, clutch/llm.py, clutch/mergequeue.py, clutch/runner.py, clutch/stages.py, tests/integration/test_daemon_composition.py]
# owner: clutch/mergequeue.py
# verified: 0a4d026b
# hash: 89c11175aa76f0cc5ee062aac1bdea053c9f7e85d922ee538e74158336133b7c

import asyncio
import json

import pytest

from clutch import runner, stages
from clutch.artifacts import Cost, StageResult
from clutch.llm import FakeLLM
from clutch.mergequeue import MergeQueue
from tests.integration.test_daemon_composition import production_writer
from tests.integration.test_mergequeue import commit, ctx, facts, ready
from tests.stages_helpers import SNAG, verdict

pytestmark = pytest.mark.disk_io_skip


def resolved(text="ok combined\n"):
    return json.dumps({"verdict": "resolved", "reason": "preserve both", "files": {"clutch/thing.py": text}})


async def conflict(ctx):
    ticket = await ready(ctx, changes={"clutch/thing.py": "ok ticket\n"})
    ctx.fs.write(ctx.repo / "clutch/thing.py", b"ok main\n")
    await commit(ctx, ctx.repo, ["clutch/thing.py"], "clutch(sibling): main edit")
    ctx.fs.write(ctx.repo / "tickets/sibling/ticket.md", b"## Goal / Why\nKeep main intent\n## Scope in / Scope out\nScope in:\nKeep the main line\nScope out:\nUnrelated\n")
    await commit(ctx, ctx.repo, ["tickets/sibling/ticket.md"], "sibling intent")
    return ticket


@pytest.mark.parametrize("mode", ["approve", "decline", "markers", "malformed", "snag", "ineligible", "inline"])
def test_admission(ctx, mode):
    async def exercise():
        ticket = await conflict(ctx)
        original_review = (ctx.repo / f"tickets/{ticket.stem}/review.md").read_bytes()
        script = {
            "approve": [resolved(), verdict()],
            "decline": [json.dumps(dict(verdict="decline", reason="intents disagree", files={}))],
            "markers": [resolved("<<<<<<< ticket\nok\n=======\nmain\n>>>>>>> main\n")],
            "malformed": ['{"wrong":"schema"}'] * (ctx.driver.retry_cap + 1),
            "snag": [resolved(), verdict("snag", [SNAG])],
            "ineligible": [],
            "inline": [],
        }[mode]
        ctx.driver.llm = FakeLLM(script)
        if mode == "ineligible":
            ctx.config.engine_plane_safety_inventory = ["clutch/"]
        queue = MergeQueue(ctx, escalate=lambda _: pytest.fail("unexpected hold"))
        result = await queue._admit(ticket, 0, conflict_ladder=mode != "inline")
        if mode == "approve":
            assert isinstance(result, StageResult) and result.outcome == "ok"  # Repair must reach squash, not handoff.
            assert (ctx.repo / "clutch/thing.py").read_text() == "ok combined\n"  # Taking ours/theirs loses intent.
            assert facts(ctx)[0].body["resolving_rung"] == "model"  # Mechanical/rework attribution would be wrong.
            assert [r.surface for r in ctx.driver.llm.requests] == ["resolve", "review"]  # Old approval alone cannot authorize.
            assert "Keep main intent" in ctx.driver.llm.requests[0].rendered  # Reading the branch ticket omits sibling intent.
            assert "+ok combined" in ctx.driver.llm.requests[1].rendered  # Review must see the resolution delta.
        elif mode == "inline":
            assert isinstance(result, StageResult) and result.outcome != "ok"
            assert len(ctx.driver.llm.requests) == 0  # Inline admission never calls resolve.
        else:
            assert result.outcome == "gate_failed" and result.findings[0].code == "merge_conflict_rerun"  # Refusals must not merge or escape as exceptions.
            assert facts(ctx)[0].body["resolving_rung"] == "rerun"
            root = ctx.worktree(ticket.stem)
            git_dir = (await ctx.git._run(root, "rev-parse", "--absolute-git-dir")).strip()
            from pathlib import Path

            assert not (Path(git_dir) / "rebase-merge").exists()  # A handed-off live rebase is unsafe.
            if mode == "decline":
                assert any("intents disagree" in f.message for f in result.findings)
            if mode == "markers":
                staged = await ctx.git._run(root, "diff", "--cached")
                assert "<<<<<<<" not in staged  # Staging before validating would leak markers.
            if mode == "snag":
                assert (ctx.repo / f"tickets/{ticket.stem}/review.md").read_bytes() == original_review
                assert not (root / f"tickets/{ticket.stem}/review.md").exists()
            if mode == "ineligible":
                assert len(ctx.driver.llm.requests) == 0  # Inventory must gate before the call.

    asyncio.run(exercise())


def test_serve_drive_allows_merge_resolution_stages(ctx, monkeypatch):
    async def exercise():
        _, writer = production_writer(ctx, [resolved(), verdict()])
        source = writer.ctx
        ticket = await conflict(source)
        # The run has already passed review; use the actual drive -> queue admission seam.
        completed = stages.StagesRun(attempt=0, results={"review": StageResult(outcome="ok", artifact=None, findings=[], cost=Cost())}, ticket_sha="ticket")

        async def run_stages(*args):
            return completed

        async def unchanged_ticket(*args, **kwargs):
            return []

        monkeypatch.setattr(runner, "run_stages", run_stages)
        monkeypatch.setattr(runner, "ticket_change_findings", unchanged_ticket)

        async def admit(ticket, *, attempt):
            writer.queue.offer(ticket, attempt=attempt)
            [result] = await writer.queue.process()
            return result

        result = await runner.drive(source, ticket, admission=admit)
        assert result == "merged"  # Rejecting admission's nested surfaces throws before the first model call.
        assert [r.surface for r in source.driver.llm.requests] == ["resolve", "review"]
        assert facts(source)[0].body["resolving_rung"] == "model"

    asyncio.run(exercise())


def test_marker_bound_accumulates_when_same_path_conflicts_again(ctx):
    async def exercise():
        def contents(value):
            return "".join(f"ok {value} {i}\n" + "".join(f"context {i} {j}\n" for j in range(10)) for i in range(11))

        ctx.fs.write(ctx.repo / "clutch/thing.py", contents("base").encode())
        await commit(ctx, ctx.repo, ["clutch/thing.py"])
        ticket = await ready(ctx, commits=[{"clutch/thing.py": contents("first")}, {"clutch/thing.py": contents("second")}])
        ctx.fs.write(ctx.repo / "clutch/thing.py", contents("main").encode())
        await commit(ctx, ctx.repo, ["clutch/thing.py"])
        ctx.driver.llm = FakeLLM([resolved(contents("main and first")), verdict()])
        result = await MergeQueue(ctx, escalate=lambda _: None)._admit(ticket, 0)
        # Each stop has 33 markers: forgetting the first stop would call resolve again.
        assert result.outcome == "gate_failed" and result.findings[0].code == "merge_conflict_rerun"
        assert [r.surface for r in ctx.driver.llm.requests] == ["resolve", "review"]
        assert facts(ctx)[0].body["resolving_rung"] == "rerun"

    asyncio.run(exercise())
