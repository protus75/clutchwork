# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that Check and merge write stage_start and stage_end events to the engine log with the right outcome, stem and attempt.
# relates: [clutch/runner.py, clutch/stages.py, clutch/tickets.py, tests/integration/test_merge.py, tests/integration/test_stages.py]
# owner: clutch/stages.py
# verified: 38957300
# hash: f5a2a2ee70331343d7d63b85c234fa6c61572abdf03f93fbc9c099bca911780d
import asyncio
import json

import pytest

from clutch import runner
from clutch.stages import run_stages
from clutch.tickets import validate_ticket
from tests.config_helpers import context, repo
from tests.stages_helpers import STEM, agent, author, verdict

pytestmark = pytest.mark.disk_io_skip


def stage_events(ctx, surface):
    log = ctx.config.state_dir / "engine.log"
    return [e for line in log.read_text().splitlines() if (e := json.loads(line)).get("surface") == surface and e["event"] in ("stage_start", "stage_end")]


def test_check_events_on_scope_violation(repo):
    author(repo)
    ctx = context(repo, [agent({"clutch/thing.py": "ok\n", "clutch/other.py": "outside\n"})])
    ticket = validate_ticket(STEM, (repo / "tickets" / STEM / "ticket.md").read_text(), repo)
    run = asyncio.run(run_stages(ctx, ticket))
    assert run.last[1].outcome == "gate_failed"  # A successful Check would not prove the violation.
    events = stage_events(ctx, "check")
    assert [(e["event"], e.get("outcome"), e["stem"], e["attempt"]) for e in events] == [
        ("stage_start", None, STEM, run.attempt),
        ("stage_end", "gate_failed", STEM, run.attempt),
    ]  # Missing, reversed, or incorrectly attributed events differ.


def test_merge_events_on_drive(repo):
    author(repo)
    ctx = context(repo, [agent({"clutch/thing.py": "ok\n"}), verdict()])
    ticket = validate_ticket(STEM, (repo / "tickets" / STEM / "ticket.md").read_text(), repo)
    assert asyncio.run(runner.drive(ctx, ticket)) == "merged"  # A stopped run never reaches admission.
    events = stage_events(ctx, "merge")
    assert [(e["event"], e.get("outcome"), e["stem"], e["attempt"]) for e in events] == [
        ("stage_start", None, STEM, 0),
        ("stage_end", "ok", STEM, 0),
    ]  # Missing, reversed, or incorrectly attributed events differ.
