# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that observe shows each surface's tier/effort from the ticket, the spec or an escalation rung, including the watch 'now' line.
# relates: [clutch/__init__.py, clutch/observe.py, clutch/specs/__init__.py, tests/integration/test_config.py]
# owner: clutch/observe.py
# verified: 38957300
# hash: 85e4b2ee25829d5bfca7dd33b0347bd785f161a14294bf9c0b7d8b784b6970e2
import json
import os
from pathlib import Path

import pytest

import clutch
import clutch.observe as watch
from clutch.specs import load_spec
from tests.config_helpers import VALID

pytestmark = pytest.mark.disk_io_skip


@pytest.fixture
def ctx(tmp_path):
    ticket = tmp_path / "tickets/alpha/ticket.md"
    ticket.parent.mkdir(parents=True)
    ticket.write_text("---\nstate: confirmed\npriority: P1\nagent_tier: low\nagent_effort: max\n---\n## Depends on\nnone\n")
    (tmp_path / "config.yaml").write_text(VALID)
    return watch.Context(tmp_path, tmp_path / "state", tmp_path / "config.yaml", None, None, None)


@pytest.fixture
def effort():
    value = load_spec((Path(clutch.__file__).parent / "specs" / "requisition_review.md").read_text()).meta.effort
    assert value != "max"  # Ticket effort must differ from the spec effort.
    return value


@pytest.fixture
def rung():
    return {"type": "cap_consumed", "ticket": "alpha", "body": {"cap": "retry", "ticket_sha": "x", "rung": {"tier": "max", "effort": "medium"}}}


def test_ticket_surfaces_show_the_ticket_capability(ctx):
    for surface in ("implement", "review", "diagnose", "rework"):
        assert watch.capability(ctx, [], "alpha", surface) == "low/max"  # Spec values and defaults differ.


def test_requisition_review_pairs_ticket_tier_with_spec_effort(ctx, effort):
    assert watch.capability(ctx, [], "alpha", "requisition_review") == f"low/{effort}"  # Neither spec tier nor ticket effort is correct.


def test_escalation_rung_shows_on_every_ticket_surface(ctx, rung, effort):
    assert watch.capability(ctx, [rung], "alpha", "review") == "max/medium (escalated)"  # Ignoring the rung differs.
    assert watch.capability(ctx, [rung], "alpha", "requisition_review") == f"max/{effort} (escalated)"  # The rung tier and spec effort both matter.


def test_operator_keep_resets_the_rung_on_review(ctx, rung):
    keep = {"type": "signal", "ticket": "alpha", "body": {"signal": "reject_verdict", "verdict": "keep", "actor": "operator"}}
    assert watch.capability(ctx, [rung, keep], "alpha", "review") == "low/max"  # A rung before keep must not survive.


def test_watch_now_line_shows_the_engine_capability(ctx, monkeypatch):
    journal = ctx.state / "journal"
    journal.mkdir(parents=True)
    (ctx.state / "clutch.lock").write_text(json.dumps({"pid": os.getpid(), "started_at": "2026-01-01T00:00:00+00:00"}))
    (journal / "000001.jsonl").write_text(json.dumps({"type": "state_transition", "ticket": "alpha", "body": {"to": "running"}, "ts": "2026-01-01T00:01:00+00:00"}) + "\n")
    (ctx.state / "engine.log").write_text(json.dumps({"event": "stage_start", "stem": "alpha", "surface": "review", "ts": "2026-01-01T00:02:00+00:00"}) + "\n")
    monkeypatch.setattr(watch, "processes", lambda ctx: [])
    monkeypatch.setattr(watch, "committed_ticket_shas", lambda ctx: {})
    assert "     asked for tier/effort low/max" in watch.text_snapshot(ctx).splitlines()  # The review spec would show high/high.


def test_resolve_uses_engine_spec_capability(ctx, rung):
    # Ticket low/max and retry max/medium must not override resolve's high/high.
    assert watch.capability(ctx, [rung], "alpha", "resolve") == "high/high"
