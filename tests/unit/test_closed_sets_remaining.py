import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from clutch import artifacts, author, status, tickets
from clutch.config import Retro, RetroMerges, RetroSettled, RetroSpikes
from clutch.journal import Event, EventType
from clutch.retro import Window, select_trigger
from tests.fakes import FakeJournal
from tests.unit.test_retro_recurrence import message


def test_closed_is_settled_plus_retired():
    assert status.CLOSED == frozenset({"merged", "already_satisfied", "rejected"})
    assert status.RETIRED == frozenset({"rejected"})


def test_major():
    assert artifacts.major("3.12") == 3
    assert artifacts.major("10.0") == 10


def test_author_skeletons_follow_kinds(monkeypatch):
    class Done(Exception):
        pass

    async def ls_files(repo):
        return ["clutch/specs/review.md"]

    async def open_tickets(checkout):
        return "none"

    async def run(stage, *args, **kwargs):
        stage.render(None, [])
        raise Done

    inputs = []
    monkeypatch.setattr(Path, "read_text", lambda self: "spec")
    monkeypatch.setattr(author, "load_spec", lambda text: SimpleNamespace(meta=SimpleNamespace(effort="medium")))
    monkeypatch.setattr(author, "render", lambda spec, values: inputs.append(values) or "rendered")
    monkeypatch.setattr(author, "list_open_tickets", open_tickets)
    monkeypatch.setattr(author, "template", lambda kind: f"template for {kind}")
    checkout = SimpleNamespace(repo=Path("/repo"), git=SimpleNamespace(ls_files=ls_files), journal=FakeJournal(), config=SimpleNamespace(routing_default_tier="medium"))
    item = message().model_copy(update={"verdict": SimpleNamespace(rationale="observed")})
    with pytest.raises(Done):
        asyncio.run(author.author(checkout, SimpleNamespace(run=run), SimpleNamespace(root=Path("/box")), item, 1))
    assert inputs[0]["skeletons"] == "\n".join(f"{kind}:\ntemplate for {kind}" for kind in tickets.KINDS)


def test_retro_settled_counts_rejected():
    events = tuple(Event(1, EventType.STATE_TRANSITION, "2026-01-01", stem, None, {"to": state}) for stem, state in (("one", "merged"), ("two", "rejected")))
    settings = Retro(merges=RetroMerges(enabled=False), settled=RetroSettled(every=2), spikes=RetroSpikes(enabled=False))
    assert select_trigger(Window("initial", events, None, 1), {"merged_count": 1, "spikes": {}}, settings, forced=False) == "settled"
