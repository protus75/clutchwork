"""Flake fixes lead eligible dispatch without overriding soft edges."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that resolved flake-fix tickets lead drain, parallel and scheduler dispatch order without overriding Runs before edges, plus the flake_fixes report filter
# relates: [clutch/config.py, clutch/drain.py, clutch/scheduler.py, tests/dispatch_settle.py, tests/unit/test_chain_order.py]
# owner: engine
# verified: 1dc2db5a
# hash: 13524a32d964cad975b93634beb5083daa5a24e66ec97387c6df9150b89b418f

import json
from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from clutch.config import Parallel
from clutch.drain import flake_fixes, order_tickets, parallel_order
from clutch.scheduler import Scheduler
from tests.dispatch_settle import dispatch_settled
from tests.unit.test_chain_order import ticket


def test_orders_and_soft_edges():
    p0 = ticket("p0", "P0")
    fix = ticket("fix", "P2")
    child = ticket("child", depends=("p0",))
    unsettled = {t.stem: t for t in (p0, fix, child)}
    assert [t.stem for t in parallel_order([p0, fix], {}, unsettled, fixes={"fix"})] == ["fix", "p0"]
    assert [t.stem for t in parallel_order([p0, fix], {}, unsettled)] == ["p0", "fix"]
    assert [t.stem for t in order_tickets([p0, fix], {}, fixes={"fix"})] == ["fix", "p0"]
    before = ticket("before", "P0", before=("fix",))
    assert [t.stem for t in order_tickets([fix, before], {}, fixes={"fix"})] == ["before", "fix"]
    assert [t.stem for t in parallel_order([fix, before], {}, {"fix": fix, "before": before}, fixes={"fix"})] == ["before", "fix"]


def test_report_filter():
    def message(link, *, status="resolved", kind="ticket", stage="check", outcome="gate_failed", message_class="failure_report"):
        return SimpleNamespace(message_class=message_class, stage=stage, outcome=outcome, status=status, resolution=SimpleNamespace(kind=kind, link=link) if status == "resolved" else None)

    messages = [
        message("fix-a"),
        message("pending", status="pending"),
        message("declined", kind="declined"),
        message("tombstone", kind="tombstone"),
        message("implement", stage="implement"),
        message("outcome", outcome="other"),
        message("class", message_class="suggestion"),
    ]
    assert flake_fixes(messages) == {"fix-a"}


@pytest.mark.asyncio
@pytest.mark.parametrize("blocked", [None, "draft", "depends", "quarantined"])
@pytest.mark.parametrize("parallel", [True, False])
async def test_scheduler_dispatch_and_queue(tmp_path, blocked, parallel):
    writes = []

    async def dispatch(ticket):
        pass

    async def sha(stem):
        return "sha"

    scheduler = Scheduler(
        SimpleNamespace(read=lambda: []),
        dispatch,
        state_dir=tmp_path,
        fs=SimpleNamespace(write=lambda path, data: writes.append((path, data))),
        clock=lambda: datetime(2026, 3, 4, tzinfo=UTC),
        caps=lambda: None,
        ticket_sha=sha,
        quarantined=lambda: {"fix"} if blocked == "quarantined" else set(),
        drought_parked=set,
        completed_unmerged=lambda: 0,
        max_unmerged=1,
    )
    scheduler.parallel = lambda: Parallel(enabled=parallel)
    scheduler.flake_fixes = lambda: {"fix"}
    fix = ticket("fix", "P2", depends=("unsettled",) if blocked == "depends" else ())
    if blocked == "draft":
        fix = replace(fix, frontmatter=fix.frontmatter.model_copy(update={"state": "draft"}))
    scheduler.update(fix)
    scheduler.update(ticket("p0", "P0"))
    chosen = await dispatch_settled(scheduler)
    expected = "fix" if blocked is None else "p0"
    assert chosen.stem == expected
    assert json.loads(writes[0][1])["order"][0] == expected
