"""Watch uses the same capability lineage as the engine."""

from types import SimpleNamespace

from clutch import observe


def test_watch_capability_restarts_at_a_supervisor_keep(tmp_path):
    ticket = tmp_path / "tickets" / "work" / "ticket.md"
    ticket.parent.mkdir(parents=True)
    ticket.write_text("---\nagent_tier: medium\nagent_effort: medium\n---\n")
    events = [{"type": "cap_consumed", "ticket": "work", "body": {"cap": "retry", "rung": {"tier": "high", "effort": "max"}}}]
    ctx = SimpleNamespace(root=tmp_path)
    assert observe.capability(ctx, events, "work", "implement") == "high/max (escalated)"
    events.append({"type": "signal", "ticket": "work", "body": {"signal": "reject_verdict", "verdict": "keep", "actor": "supervisor"}})
    assert observe.capability(ctx, events, "work", "implement") == "medium/medium"
