# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests triage settling with a single model and with a majority-verdict panel, covering majority votes, tie-breaks and links, dropped or failed members, the panel_facts journal signal, and the reopen and rejected-link guards
# relates: [clutch/artifacts.py, clutch/driver.py, clutch/panel.py, clutch/triage.py, tests/unit/test_route_kinds_filter.py]
# owner: engine
# verified: 90b9b520
# hash: 13d7a92c24d54ab741b4e26c6c1ab378113c40020f5f2f3cea90504edf872df7
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from clutch import triage
from clutch.artifacts import Cost, Finding, StageResult
from clutch.driver import PanelResult, ProviderDroughtResult
from clutch.panel import DroppedMember
from tests.fakes import FakeJournal
from tests.unit.test_route_kinds_filter import config


def cfg(size=None):
    panel = f", panel: {{size: {size}, combine: majority-verdict}}" if size else ""
    return config("  - {tier: medium, surface: triage, candidates: [{provider: codex, model: a}]" + panel + "}\n")


def reply(verdict, label, link=None, days=14):
    return triage.TriageReply(verdict=verdict, link=link, summary="S" + label, rationale="R" + label, evidence=["e" + label], reopen_after_days=None if verdict == "author" else days)


def member(value):
    return StageResult("ok", value, [], Cost())


@pytest.fixture
def setup(tmp_path, monkeypatch):
    message = SimpleNamespace(
        id="box-1",
        seq=7,
        reopen=False,
        verdict=None,
        message_class="suggestion",
        summary="concern",
        origin="test",
        stage=None,
        outcome=None,
        retro_report_key=None,
        fixed_failure=None,
        overcorrection_risk=None,
        proposed_spec_paths=[],
        test_issue=None,
        conflict_action=None,
        proposed_paths=[],
        report=None,
        resolution=None,
    )
    box = SimpleNamespace(pending=lambda: [message], messages=lambda: [message], get=lambda _: message, root=tmp_path, record_verdict=Mock())
    record = AsyncMock(return_value="recorded")
    author = AsyncMock(return_value=SimpleNamespace(stem="new-ticket", declined=None))
    neighbors = AsyncMock(return_value="neighbors")
    for name, value in dict(
        recover_retro_ticket=AsyncMock(return_value=None),
        read_registry=lambda _: [],
        list_open_tickets=AsyncMock(return_value="open"),
        neighbors_block=neighbors,
        committed=AsyncMock(return_value=True),
        is_rejected=AsyncMock(return_value=False),
        _record=record,
        author=author,
    ).items():
        monkeypatch.setattr(triage, name, value)
    spec = SimpleNamespace(meta=SimpleNamespace(effort="low", version="1"))

    async def run(size=None, single=None, panel=None, routing=True):
        c = cfg(size)
        if not routing:
            c.routing = []
        checkout = SimpleNamespace(repo=tmp_path, config=c)
        driver = SimpleNamespace(run=AsyncMock(return_value=single), run_panel=AsyncMock(return_value=panel), log=SimpleNamespace(event=Mock()), journal=FakeJournal())
        lines = await triage._settle_pass(checkout, driver, box, spec, [], 4, frozenset())
        return checkout, driver, lines

    return SimpleNamespace(run=run, message=message, box=box, record=record, author=author, neighbors=neighbors, spec=spec)


@pytest.mark.asyncio
@pytest.mark.parametrize("size", [None, 1])
async def test_single(setup, size):
    value = reply("declined", "0")
    c, d, lines = await setup.run(size, single=member(value))
    # Wrong: changing the existing call arguments or routing a single member through the panel.
    assert d.run.await_args.kwargs == dict(
        ticket=None, subject="box-1", run_seq=7, attempt=4, workspace=c.repo, tier="medium", effort="low", stuck_budget=600.0, expected_budget="surface", scope_fence=()
    )
    d.run.assert_awaited_once()
    d.run_panel.assert_not_awaited()
    assert lines == [("box-1", "recorded")]
    assert setup.record.await_args.args[4:] == ("declined", "box-1", value, "concern")
    d.log.event.assert_not_called()
    assert d.journal.events == []
    setup.record.reset_mock()
    _, d, lines = await setup.run(size, single=StageResult("timeout", None, [], Cost()))
    assert lines == [("box-1", "box-1: timeout; remains pending")]
    setup.record.assert_not_awaited()
    setup.author.assert_not_awaited()
    d.log.event.assert_not_called()
    assert d.journal.events == []


@pytest.mark.asyncio
async def test_majorities_and_inputs(setup):
    first, other = reply("declined", "0"), reply("declined", "2", days=30)
    c, d, lines = await setup.run(3, panel=PanelResult([member(first), member(reply("author", "1")), member(other)], []))
    assert lines == [("box-1", "recorded")]
    assert setup.record.await_args.args[4:] == ("declined", "box-1", first, "concern")
    setup.author.assert_not_awaited()
    setup.neighbors.assert_awaited_once_with(c, "concern", "box-1")
    (event,) = d.journal.events
    assert (event.type, event.ticket, event.key) == ("signal", None, None)
    d.log.event.assert_not_called()
    assert event.body == dict(
        signal="panel_facts",
        box_id="box-1",
        attempt=4,
        surface="triage",
        combiner="majority-verdict",
        member_count=3,
        members=[dict(provider="codex", model="a", verdict=v) for v in ("declined", "author", "declined")],
        verdict_counts={"declined": 2, "author": 1},
        dropped=[],
        merged=[],
        kept_index=None,
        agreement_kind="samples",
    )
    _, single, _ = await setup.run(single=member(first))
    assert d.run_panel.await_args.kwargs == dict(single.run.await_args.kwargs, size=3)
    _, fallback, _ = await setup.run(single=member(first), routing=False)
    fallback.run.assert_awaited_once()
    fallback.run_panel.assert_not_awaited()
    setup.record.reset_mock()
    a = reply("author", "0")
    await setup.run(3, panel=PanelResult([member(a), member(reply("author", "1")), member(reply("tombstone", "2", "target"))], []))
    assert setup.box.record_verdict.call_args.args[1].rationale == "R0"
    setup.author.assert_awaited_once()
    setup.record.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("values", "winner", "kind", "link"),
    [
        ([reply("author", "0"), reply("declined", "1")], 1, "declined", "box-1"),
        ([reply("author", "0"), reply("tombstone", "1", "target"), reply("declined", "2")], 2, "declined", "box-1"),
        ([reply("author", "0"), reply("tombstone", "1", "target")], 1, "tombstone", "target"),
        ([reply("tombstone", "0", "a"), reply("tombstone", "1", "b"), reply("declined", "2")], 0, "tombstone", "a"),
    ],
)
async def test_ties_and_links(setup, values, winner, kind, link):
    await setup.run(len(values), panel=PanelResult([member(v) for v in values], []))
    assert setup.record.await_args.args[4:7] == (kind, link, values[winner])
    setup.author.assert_not_awaited()
    setup.box.record_verdict.assert_not_called()


@pytest.mark.asyncio
async def test_drops_and_failures(setup):
    dropped = [DroppedMember(index=0, failure_class="infra_error")]
    value = reply("declined", "1")
    _, d, _ = await setup.run(2, panel=PanelResult([member(value)], dropped))
    assert setup.record.await_args.args[6] == value
    assert d.journal.events[0].body["dropped"] == [{"index": 0, "failure_class": "infra_error"}]
    assert d.journal.events[0].body["member_count"] == 2
    await setup.run(2, panel=PanelResult([member(reply("author", "1"))], dropped))
    setup.author.assert_awaited_once()
    setup.author.reset_mock()
    setup.record.reset_mock()
    quota = Finding(code="quota_exhausted", message="quota", paved_road="wait")
    lines = []
    for findings in ([quota], []):
        _, d, line = await setup.run(2, panel=PanelResult([], dropped + [DroppedMember(index=1, failure_class="infra_error")], findings))
        lines.append(line)
        d.log.event.assert_not_called()
        assert d.journal.events == []
    _, d, line = await setup.run(single=StageResult("infra_error", None, [quota], Cost()))
    assert lines == [line, line] == [[("box-1", "box-1: infra_error; remains pending")]] * 2
    d.log.event.assert_not_called()
    assert d.journal.events == []
    for bad in (StageResult("timeout", None, [], Cost()), ProviderDroughtResult("infra_error", None, [], Cost(), {"providers": ["codex"]})):
        _, d, line = await setup.run(2, panel=PanelResult([member(value), bad], []))
        assert line == [("box-1", f"box-1: {bad.outcome}; remains pending")]
        d.log.event.assert_not_called()
        assert d.journal.events == []
    setup.record.assert_not_awaited()
    setup.author.assert_not_awaited()


@pytest.mark.asyncio
async def test_guards(setup, monkeypatch):
    value = reply("tombstone", "0", "target")
    setup.message.reopen = True
    await setup.run(2, panel=PanelResult([member(value), member(value)], []))
    setup.author.assert_awaited_once()
    assert setup.box.record_verdict.call_args.args[1].rationale == "R0"
    setup.message.reopen = False
    monkeypatch.setattr(triage, "is_rejected", AsyncMock(return_value=True))
    await setup.run(2, panel=PanelResult([member(value), member(value)], []))
    args = setup.record.await_args.args
    assert args[4:6] == ("declined", "box-1")
    assert args[6].evidence == ["e0", "unresolvable link: target"]
