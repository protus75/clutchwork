# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests supervised Rework: the supervise block renders its trigger and lessons, the edit gate refuses forbidden edits before review, and apply_rework forwards supervise
# relates: [clutch/artifacts.py, clutch/daemon.py, clutch/llm.py, clutch/rework.py, clutch/specs/__init__.py, tests/integration/test_mergequeue.py]
# owner: clutch/rework.py
# verified: d32c32ad
# hash: 15cad81d74e4810ec797da683bc0e9d1ee9cf05cf7d5f12a6e2dda668a306acf
import pytest

from clutch import daemon
from clutch.artifacts import Cost, StageResult
from clutch.llm import FakeLLM
from clutch.rework import REWORK_ORDER, ReworkOrder, ReworkReply, Supervise, rework
from clutch.specs import data_close, data_open
from tests.integration.test_mergequeue import ctx
from tests.integration.test_rework import SNAG, order, original, requisition, run, signals, ticket_bytes

pytestmark = pytest.mark.disk_io_skip

S = Supervise("premise_bounce cap spent", ("Fence tests/x.py",))


async def invoke(ctx, ticket, text, script, supervise=None, attempt=0):
    ctx.driver.llm = FakeLLM(script)
    result = await rework(ctx, ticket, text, [SNAG], attempt=attempt, workspace=ctx.repo, tier="max", effort="medium", stuck_budget=42, supervise=supervise)
    return result, ctx.driver.llm.requests


def test_supervise_block_renders_trigger_and_lessons(ctx):
    async def scenario():
        ticket, text = await original(ctx)
        for attempt, (value, expected) in enumerate([(S, '{"lessons": ["Fence tests/x.py"], "trigger": "premise_bounce cap spent"}'), (None, "none")]):
            _, requests = await invoke(ctx, ticket, text, [order()], value, attempt)
            assert f"{data_open('supervise')}\n{expected}\n{data_close('supervise')}" in requests[0].rendered

    run(scenario())


@pytest.mark.parametrize("case", ["split", "unchanged", "goal", "criterion"])
def test_gate_refusal_ends_before_review(ctx, case):
    async def scenario():
        ticket, text = await original(ctx)
        text = text.strip()
        before = ticket_bytes(ctx)
        proposals = {
            "split": order("split", [("one", text), ("two", text)]),
            "unchanged": order("update", [("original", text)]),
            "goal": order("update", [("original", text.replace("`thing.py` holds the word ok.", "Changed goal."))]),
            "criterion": order("update", [("original", text.replace("1. `grep -q ok clutch/thing.py` exits 0.\n", ""))]),
        }
        reply = proposals[case]
        ctx.driver.retry_cap = 1
        result, requests = await invoke(ctx, ticket, text, [reply], S)
        assert result.outcome == "gate_failed"
        assert result.findings and all(f.code == "supervise_edit" for f in result.findings)
        assert [r.surface for r in requests] == ["rework"]
        assert result.artifact == ReworkReply.model_validate_json(reply)
        assert signals(ctx, REWORK_ORDER) == []
        assert ticket_bytes(ctx) == before

    run(scenario())


def test_allowed_update_is_reviewed(ctx):
    async def scenario():
        ticket, text = await original(ctx)
        revised = text.replace("In: thing. Out: the rest.", "In: the thing. Out: the rest.")
        result, requests = await invoke(ctx, ticket, text, [order("update", [("original", revised)]), requisition()], S)
        assert result.outcome == "ok"
        assert isinstance(result.artifact, ReworkOrder) and result.artifact.action == "update"
        assert [r.surface for r in requests].count("requisition_review") == 1
        assert len(signals(ctx, REWORK_ORDER)) == 1

    run(scenario())


def test_review_snag_returns_the_last_proposal(ctx):
    async def scenario():
        ticket, text = await original(ctx)
        revised = text.replace("In: thing. Out: the rest.", "In: the thing. Out: the rest.")
        reply = order("update", [("original", revised)])
        ctx.driver.retry_cap = 0
        for attempt, value in enumerate((S, None)):
            result, _ = await invoke(ctx, ticket, text, [reply, requisition("snag")], value, attempt)
            assert result.outcome == "gate_failed"
            assert result.artifact == (ReworkReply.model_validate_json(reply) if value else None)
            assert SNAG.message in [f.message for f in result.findings]

    run(scenario())


def test_apply_rework_forwards_supervise(ctx, monkeypatch):
    async def scenario():
        ticket, _ = await original(ctx)
        ctx.worktree("original").mkdir(parents=True)
        expected = StageResult(outcome="gate_failed", artifact=None, findings=[SNAG], cost=Cost())
        seen = []

        async def recorder(*args, **kwargs):
            seen.append(kwargs["supervise"])
            return expected

        monkeypatch.setattr(daemon, "rework", recorder)
        assert await daemon.apply_rework(ctx, ticket, [SNAG], attempt=0, supervise=S) is expected
        assert await daemon.apply_rework(ctx, ticket, [SNAG], attempt=0) is expected
        assert seen[0] is S and seen[1] is None

    run(scenario())
