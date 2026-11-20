"""Overruled implement premises escalate and retain their retry rung."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Overruled implement premises escalate and retain their retry rung.
# relates: [clutch/config.py, clutch/drain.py, clutch/journal.py, clutch/runner.py]
# owner: engine
# verified: 9a610809
# hash: 603d20edf586edeb0a1899a33c6dc7f25176986c250e30fabff6ed62205481ce

from types import SimpleNamespace

import pytest

from clutch import runner
from clutch.config import Caps
from clutch.drain import parked_blob, record_reoffer
from clutch.journal import Event, EventType


class MemoryJournal:
    def __init__(self, events=()):
        self.events = list(events)

    def read(self):
        return list(self.events)

    def append(self, kind, body, *, ticket):
        self.events.append(Event(1, kind, "time", ticket, None, body))


def event(body):
    return Event(1, EventType.STATE_TRANSITION, "time", "work", None, body)


@pytest.mark.parametrize(
    "body,held",
    [
        ({"to": "premise_failed", "stage": "implement", "dispatch": "escalate"}, None),
        ({"to": "premise_failed", "stage": "implement", "dispatch": "retry"}, "ran-sha"),
        ({"to": "premise_failed", "stage": "implement", "dispatch": "reject_queue"}, "ran-sha"),
        ({"to": "premise_failed", "stage": "implement"}, "ran-sha"),
        ({"to": "premise_failed", "stage": "requisition", "dispatch": "escalate"}, "ran-sha"),
    ],
)
def test_park_and_reoffer(body, held):
    rung = {"tier": "high", "effort": "max"}
    body = {**body, "rung": rung}
    history = [event({"to": "running", "ticket_sha": "ran-sha"}), event(body)]
    assert parked_blob(history, "work") == held
    journal = MemoryJournal()
    record_reoffer(journal, history, "work", "new-sha")
    draws = [e.body for e in journal.events if e.type == EventType.CAP_CONSUMED]
    assert draws == ([{"cap": "retry", "ticket_sha": "new-sha", "rung": rung}] if held is None else [])


@pytest.mark.asyncio
@pytest.mark.parametrize("rung", [{"tier": "high", "effort": "medium"}, None])
async def test_failure_terminal_routes_overruled_premise(monkeypatch, rung):
    journal = MemoryJournal()
    ticket = SimpleNamespace(stem="work", frontmatter=SimpleNamespace(agent_tier="medium", agent_effort="medium"))
    ctx = SimpleNamespace(driver=SimpleNamespace(journal=journal), config=SimpleNamespace(caps=Caps(premise_bounce=2)), worktree=lambda _: SimpleNamespace(exists=lambda: False))
    monkeypatch.setattr(runner, "next_rung", lambda config, tier, effort: rung)
    await runner.failure_terminal(ctx, ticket, outcome="premise_failed", stage="implement", findings=[], attempt=0, verdict="retry")
    terminal = journal.events[-1].body
    assert terminal["dispatch"] == ("escalate" if rung else "reject_queue")
    assert terminal.get("rung") == rung
