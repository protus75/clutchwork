"""Watch uses the same capability lineage as the engine."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the watch capability display uses the same lineage as the engine: an escalated rung resets after a supervisor keep.
# relates: [clutch/observe.py]
# owner: clutch/observe.py
# verified: d32c32ad
# hash: e805c5600ec562786b639c5e75aaf9cab46b9688f17bfa561dbb957cbabca2d3

from types import SimpleNamespace

import pytest

from clutch import observe

pytestmark = pytest.mark.disk_io_skip


def test_watch_capability_restarts_at_a_supervisor_keep(tmp_path):
    ticket = tmp_path / "tickets" / "work" / "ticket.md"
    ticket.parent.mkdir(parents=True)
    ticket.write_text("---\nagent_tier: medium\nagent_effort: medium\n---\n")
    events = [{"type": "cap_consumed", "ticket": "work", "body": {"cap": "retry", "rung": {"tier": "high", "effort": "max"}}}]
    ctx = SimpleNamespace(root=tmp_path)
    assert observe.capability(ctx, events, "work", "implement") == "high/max (escalated)"
    events.append({"type": "signal", "ticket": "work", "body": {"signal": "reject_verdict", "verdict": "keep", "actor": "supervisor"}})
    assert observe.capability(ctx, events, "work", "implement") == "medium/medium"
