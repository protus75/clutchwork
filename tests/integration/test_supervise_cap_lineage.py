"""Watch uses the same capability lineage as the engine."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Watch uses the same capability lineage as the engine.
# relates: [clutch/observe.py]
# owner: clutch/observe.py
# verified: 96e46658
# hash: fe8f89442fdfc57bc27d5993cc63a74501766fc7f589787ac517ac1f38b521d0

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
