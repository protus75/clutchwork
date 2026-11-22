# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Check stage emits exactly one stage_start/stage_end event pair with its outcome, whether called directly or through run_stages
# relates: [clutch/artifacts.py, clutch/stages.py, tests/fakes.py]
# owner: engine
# verified: d80fccb7
# hash: 71cd2c6d3fc133ad943ed06734639b17a2f501fd0363bfa03d56fddf22d4d4d6
import asyncio
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from clutch import stages
from clutch.artifacts import Finding
from tests.fakes import FakeClock, FakeJournal


def test_check_events_direct_and_pipeline(monkeypatch):
    events = []
    clock = FakeClock()

    @contextmanager
    def stage(**fields):
        events.append(("stage_start", fields))
        yield SimpleNamespace(end=lambda outcome: events.append(("stage_end", {**fields, "outcome": outcome})))

    driver = SimpleNamespace(stage=stage, clock=clock, provider_wait=lambda *args: 0, journal=FakeJournal(clock))
    ctx = SimpleNamespace(
        driver=driver, config=SimpleNamespace(review=SimpleNamespace(autofix=[]), meta=SimpleNamespace(paths=[])), worktree=lambda stem: Path("/work"), boundary=stages.StageBoundary()
    )
    ticket = SimpleNamespace(stem="work")
    slip = stages.PackingSlip(produced_by_spec_version=1, produced_at_sha="head", stem="work", branch="work", outcome="ok", summary="work", run_record="run.md")
    monkeypatch.setattr(stages, "check_candidates", AsyncMock(return_value=[Finding(code="candidate_paths", message="refused", paved_road="fix")]))
    monkeypatch.setattr(stages, "ticket_change_findings", AsyncMock(return_value=[]))

    def verify(result):
        assert result.outcome == "gate_failed"
        assert events == [("stage_start", {"stem": "work", "attempt": 2, "surface": "check"}), ("stage_end", {"stem": "work", "attempt": 2, "surface": "check", "outcome": result.outcome})]

    verify(asyncio.run(stages.check(ctx, ticket, slip, attempt=2)))
    events.clear()
    ctx.boundary.run = stages.StagesRun(attempt=2, results={"implement": stages.StageResult(outcome="ok", artifact=slip, findings=[], cost=stages.Cost())}, ticket_sha="head")
    run = asyncio.run(stages.run_stages(ctx, ticket))
    verify(run.results["check"])
