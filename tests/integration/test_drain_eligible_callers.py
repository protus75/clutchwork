from types import SimpleNamespace as NS

from clutch import drain
from clutch.journal import Event, EventType


def test_budget_and_drought_side_effects_follow_sort_order(monkeypatch):
    def ticket(stem, priority, stuck):
        return NS(stem=stem, frontmatter=NS(state="confirmed", priority=priority, agent_tier="medium", agent_effort="medium"), depends=(), runs_before=(), stuck_minutes=stuck)

    late, early, costly = ticket("late", "P2", 1), ticket("early", "P0", 1), ticket("costly", "P1", 11)
    parks = []
    deadlines = iter(["early-deadline", "late-deadline"])
    providers = NS(active=True, drought=lambda *args: NS(deadline=next(deadlines)), park=lambda stem, drought: parks.append((stem, drought.deadline)))
    config = NS(caps=NS(), drain=NS(max_ticket_minutes=10))
    control = NS(projection=NS(stop_requested=False), storm_holds=dict, providers=providers)
    run = drain._Drain(NS(config=config, control=control), None, frozenset(), deadline=object())
    monkeypatch.setattr(drain.caps, "spent", lambda config, events, stem: "retry" if stem == "costly" else None)
    events = [Event(1, EventType.STATE_TRANSITION, "2026-01-01T00:00:00+00:00", "costly", None, {"to": "gate_failed"})]
    scan = drain._Scan({t.stem: t for t in [late, costly, early]}, {}, ())
    result = run._select(scan, events, {"costly": "gate_failed"}, {"costly"})
    assert result == (None, False)  # Drought parks both otherwise dispatchable tickets.
    assert "costly" in run.over_budget  # Filtering held or spent re-offers first loses this park.
    assert parks == [("early", "early-deadline"), ("late", "late-deadline")]  # Input order is the reverse of priority order.
    assert run.provider_deadlines == ["early-deadline", "late-deadline"]  # Deadlines follow the same sorted traversal.
