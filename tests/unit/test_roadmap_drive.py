from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import __main__ as cli
from clutch import roadmap, triage
from clutch.journal import EventType
from clutch.runner import Refusal
from clutch.seams import NotificationFailed
from tests.fakes import FakeJournal
from tests.unit.test_phase_events import RecordingLog


class Notifications:
    def __init__(self):
        self.calls = []

    async def notify(self, argv):
        self.calls.append(argv)
        return {"rc": 0}


@pytest.fixture
def setup(tmp_path, monkeypatch):
    (tmp_path / "docs").mkdir()
    (tmp_path / roadmap.ROADMAP).touch()
    journal = FakeJournal()
    for stem, body in [("a", {"to": "merged"}), ("b", {"to": "gate_failed", "routed": "reject_queue", "reason": "premise"}), ("c", {"to": "merged"})]:
        journal.append(EventType.STATE_TRANSITION, body, ticket=stem)
    journal.append(EventType.EFFECT_COMPLETION, {"cost": {"usd": 1.5}})
    checkout = SimpleNamespace(repo=tmp_path, journal=journal, config=SimpleNamespace(notify=["say"]))
    calls = []

    async def author(*args):
        calls.append(("author", *args))
        return ["authored x"]

    async def ship(*args):
        calls.append(("ship", *args))
        return ["gate ok"]

    async def status(*args):
        calls.append(("status", *args))
        return ["release 1.0.0: ...", "next: r"]

    monkeypatch.setattr(roadmap, "author_ahead", author)
    monkeypatch.setattr(roadmap, "ship", ship)
    monkeypatch.setattr(roadmap, "status", status)
    return checkout, calls, Notifications(), RecordingLog(), AsyncMock()


@pytest.mark.asyncio
async def test_drive_order_and_digest(setup):
    c, calls, notify, log, author = setup
    result = await roadmap.drive(c, author_messages=author, notifications=notify, log=log)
    expected = ["roadmap digest 3", "merged: c", "held: b (premise)", "release 1.0.0: ...", "next: r", "authored x", "gate ok", "spend: $1.50"]
    assert calls == [("author", c, 2, author), ("ship", c), ("status", c)]
    assert notify.calls == [["say", "\n".join(expected)]]
    assert result == expected
    assert [(e.type, e.key) for e in c.journal.read()[-2:]] == [(EventType.EFFECT_INTENT, "notify/roadmap/digest/3"), (EventType.EFFECT_COMPLETION, "notify/roadmap/digest/3")]
    assert log.events == [("roadmap_drive", {"lines": expected})]


@pytest.mark.asyncio
async def test_digest_since_last_digest(setup):
    c, _, notify, log, author = setup
    await roadmap.drive(c, author_messages=author, notifications=notify, log=log)
    c.journal.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="d")
    await roadmap.drive(c, author_messages=author, notifications=notify, log=log)
    assert notify.calls[-1][1].splitlines()[1] == "merged: d"
    before = c.journal.read()
    await roadmap.drive(c, author_messages=author, notifications=notify, log=log)
    assert len(notify.calls) == 2
    assert c.journal.read() == before


@pytest.mark.asyncio
async def test_drive_edges(setup, monkeypatch):
    c, calls, notify, log, author = setup
    path = c.repo / roadmap.ROADMAP
    path.unlink()
    before = c.journal.read()
    assert await roadmap.drive(c, author_messages=author, notifications=notify, log=log) == []
    assert calls == [] and notify.calls == [] and c.journal.read() == before
    path.touch()
    monkeypatch.setattr(roadmap, "author_ahead", AsyncMock(side_effect=Refusal("dirty", "commit it")))
    c.config.notify = None
    result = await roadmap.drive(c, author_messages=author, notifications=notify, log=log)
    assert "roadmap: dirty -- commit it" in result
    assert [call[0] for call in calls] == ["ship", "status"]
    assert not notify.calls and c.journal.read() == before
    assert log.events[-1] == ("roadmap_drive", {"lines": result})
    c.config.notify = ["say"]
    notify.notify = AsyncMock(side_effect=NotificationFailed("boom"))
    await roadmap.drive(c, author_messages=author, notifications=notify, log=log)
    assert ("notify_failed", {"key": "notify/roadmap/digest/3", "error": "boom"}) in log.events
    monkeypatch.setattr(roadmap, "ship", AsyncMock(side_effect=RuntimeError("ship")))
    with pytest.raises(RuntimeError, match="ship"):
        await roadmap.drive(c, author_messages=author, notifications=notify, log=log)


@pytest.mark.asyncio
async def test_build_driver_composes(tmp_path, monkeypatch):
    c = SimpleNamespace(repo=tmp_path, env={}, config=SimpleNamespace(notify=["say"]), control=SimpleNamespace(providers=object()))
    log, llm = object(), object()
    preflight = AsyncMock(return_value=llm)
    triage_pass = AsyncMock()
    monkeypatch.setattr(cli, "_preflighted_llm", preflight)
    monkeypatch.setattr(triage, "triage_pass", triage_pass)
    monkeypatch.setattr(cli, "child_env", lambda *a, **k: {})
    monkeypatch.setattr(cli.Redactor, "from_config", lambda *a: SimpleNamespace(scrub=str))

    async def drive(checkout, *, author_messages, notifications, log):
        assert checkout is c and notifications.cwd == tmp_path and log is marker
        await author_messages(["box-1"])
        return ["done"]

    marker = log
    monkeypatch.setattr(roadmap, "drive", drive)
    assert await cli.build_driver()(c, log) == ["done"]
    preflight.assert_awaited_once_with(c, c.control.providers)
    triage_pass.assert_awaited_once_with(c, llm, frozenset({"box-1"}))
    assert cli._parser().parse_args(["roadmap", "author"]).ahead == roadmap.AHEAD == 2
