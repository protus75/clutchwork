"""Supervisor keeps reset ordinary budgets but not their own bound."""

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from clutch import caps
from clutch.audit import audit
from clutch.config import Caps
from clutch.journal import Event, EventType


def event(kind, body, ticket="work"):
    return Event(1, kind, "time", ticket, None, body)


def keep(actor):
    return event(EventType.SIGNAL, {"signal": "reject_verdict", "verdict": "keep", "actor": actor})


def draw(cap, **extra):
    return event(EventType.CAP_CONSUMED, {"cap": cap, **extra})


def test_supervisor_keep_starts_a_lineage():
    events = [event(EventType.STATE_TRANSITION, {"to": "running"}), event(EventType.STATE_TRANSITION, {"to": "gate_failed", "stage": "check"}), *[draw("retry") for _ in range(3)]]
    assert caps.spent(Caps(), events, "work") == "retry"
    tail = draw("infra")
    assert caps.lineage([*events, keep("supervisor"), tail], "work") == (tail,)
    assert caps.failed_attempts([*events, keep("supervisor"), tail], "work") == 0
    assert caps.spent(Caps(), [*events, keep("supervisor"), tail], "work") is None
    assert caps.spent(Caps(), [*events, keep("machine")], "work") == "retry"


def test_supervisor_keep_resets_capability():
    ticket = SimpleNamespace(stem="work", frontmatter=SimpleNamespace(agent_tier="medium", agent_effort="medium"))
    events = [draw("retry", rung={"tier": "high", "effort": "max"})]
    assert caps.capability(ticket, events) == ("high", "max")
    assert caps.capability(ticket, [*events, keep("supervisor")]) == ("medium", "medium")


def test_supervise_draws_count_since_the_operator_keep():
    events = [draw("supervise"), keep("supervisor"), draw("supervise"), keep("supervisor")]
    assert caps.supervise_draws(events, "work") == 2
    assert caps.draws(events, "work", "supervise") == 0
    assert caps.supervise_draws([*events, keep("machine")], "work") == 2
    assert caps.supervise_draws([*events, keep("operator")], "work") == 0


def test_supervise_cap_is_declared_and_never_routes():
    assert Caps().supervise == 2
    with pytest.raises(ValidationError):
        Caps(supervise=0)
    assert "supervise" in caps.DECLARED_CAPS
    assert "supervise" not in caps.CAPS
    assert caps.spent(Caps(supervise=1), [draw("supervise"), draw("supervise")], "work") is None

    class MemoryJournal:
        def __init__(self):
            self.events = []

        def append(self, kind, body, *, ticket):
            self.events.append(event(kind, body, ticket))

    journal = MemoryJournal()
    caps.consume(journal, "work", "supervise", "sha")
    assert len(journal.events) == 1
    assert journal.events[0].type == EventType.CAP_CONSUMED
    assert journal.events[0].body == {"cap": "supervise", "ticket_sha": "sha"}
    assert not [v for v in audit([(journal.events[0],)]) if v.code == "declared_cap"]
