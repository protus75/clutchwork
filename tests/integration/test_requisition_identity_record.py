"""Approval fixture records the same identity inside and outside an event loop."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Integration tests checking that the approval fixture, CLI review, drain dispatch, Author and rework all record the same 64-hex requisition_verdict input_identity in the journal.
# relates: [clutch/config.py, clutch/journal.py, clutch/llm.py, clutch/runner.py, tests/approval.py, tests/integration/test_author.py]
# owner: engine
# verified: 9c24a9bd
# hash: c24804fd2163fe3fab679afab1f8a376d21a7badf4b34fe80367c07342407a06

import asyncio
import re

from clutch.journal import EventType, Journal
from tests.approval import approve
from tests.integration.test_cli import git_out
from tests.integration.test_drain import Clock, commit_ticket, confirmed, make_root
from tests.integration.test_mergequeue import ctx  # noqa: F401


def test_fixture_event_loop_identity(tmp_path):
    root = make_root(tmp_path)
    config = root / "config.yaml"
    config.write_text(config.read_text().replace("review: {}", "  - {tier: medium, surface: review, candidates: [{provider: claude}]}\nreview: {}"))
    git_out(root, "add", "config.yaml")
    git_out(root, "commit", "-m", "review route")
    commit_ticket(root, "candidate", confirmed())
    clock = Clock()
    approve(root, "candidate", clock)

    async def inside():
        approve(root, "candidate", clock)

    asyncio.run(inside())
    events = [e for e in Journal(root / ".clutch/state", clock).read() if e.type == EventType.SIGNAL and e.body.get("signal") == "requisition_verdict"]
    assert len(events) == 2
    assert re.fullmatch(r"[0-9a-f]{64}", events[0].body["input_identity"])
    assert events[0].body["input_identity"] == events[1].body["input_identity"]


def test_cli_dispatch_and_fixture_share_identity(tmp_path, monkeypatch):
    from clutch import runner
    from clutch.llm import FakeLLM
    from tests.integration.test_drain import pause_checkout
    from tests.integration.test_requisition_gate import dispatch, reply
    from tests.integration.test_review_command import run

    root = make_root(tmp_path)
    config = root / "config.yaml"
    config.write_text(config.read_text().replace("review: {}", "  - {tier: medium, surface: review, candidates: [{provider: claude}]}\nreview: {}"))
    git_out(root, "add", "config.yaml")
    git_out(root, "commit", "-m", "review route")
    commit_ticket(root, "gate", confirmed())
    snag = reply("snag", "scope")
    assert run(root, monkeypatch, FakeLLM([snag]), "gate") == 1
    checkout = pause_checkout(root)
    writer = runner.bind(checkout, FakeLLM([snag]))
    assert asyncio.run(dispatch(root, checkout, writer)) == "premise_failed"
    approve(root, "gate", checkout.clock)
    events = [e for e in checkout.journal.read() if e.body.get("signal") == "requisition_verdict"]
    identities = [e.body["input_identity"] for e in events]
    assert len(identities) == 3
    assert re.fullmatch(r"[0-9a-f]{64}", identities[0])
    assert identities == [identities[0]] * 3


def test_author_records_identity(tmp_path, monkeypatch):
    from clutch.llm import FakeLLM
    from tests.integration.test_author import _box, _events, _failure, _routes, _run, requisition_reply
    from tests.integration.test_triage import author_reply, reply

    root = make_root(tmp_path)
    _routes(root)
    _failure(_box(root))
    assert _run(root, monkeypatch, FakeLLM([reply("author"), author_reply("repair-thing"), requisition_reply("approve")])) == 0
    events = [e for e in _events(root) if e.body.get("signal") == "requisition_verdict"]
    assert len(events) == 1
    assert re.fullmatch(r"[0-9a-f]{64}", events[0].body["input_identity"])
    from clutch.requisition import review_input_identity
    from clutch.runner import SPECS_DIR
    from clutch.tickets import validate_ticket
    from tests.integration.test_drain import pause_checkout

    checkout = pause_checkout(root)
    text = (root / "tickets/repair-thing/ticket.md").read_text()
    ticket = validate_ticket("repair-thing", text, root)
    expected = asyncio.run(review_input_identity(root, text, ticket, checkout.config, checkout.git, SPECS_DIR, None, checkout.journal.read(), tier="medium"))
    assert expected == events[0].body["input_identity"]


def test_rework_records_identity(ctx):
    from clutch.config import Route
    from tests.integration.test_rework import invoke, order, original, requisition, signals

    ctx.config.routing.append(Route(tier="max", surface="review", candidates=ctx.config.routing[1].candidates))

    async def scenario():
        ticket, text = await original(ctx)
        result, _ = await invoke(ctx, ticket, text, [order("update", [(ticket.stem, text)]), requisition()])
        assert result.outcome == "ok"
        [event] = signals(ctx, "requisition_verdict")
        assert re.fullmatch(r"[0-9a-f]{64}", event.body["input_identity"])
        from clutch.requisition import review_input_identity

        expected = await review_input_identity(ctx.repo, result.artifact.tickets[0].ticket, ticket, ctx.config, ctx.git, ctx.specs_dir, None, ctx.driver.journal.read(), tier="max")
        assert event.body["input_identity"] == expected

    asyncio.run(scenario())
