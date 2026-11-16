import asyncio
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from clutch import merge, stages
from clutch.artifacts import Finding
from clutch.gates import GateRunResult
from clutch.git import GitError
from clutch.mergequeue import MergeQueue


def evidence():
    return stages.Evidence(stem="work", head_sha="branch", claimed="ok", scope_fence=["src"], changed_files=["src/a"], inserted_lines=3, verification=[], run_record="record")


def test_gather_uses_supplied_safety(monkeypatch):
    given = evidence()
    gather = AsyncMock(side_effect=AssertionError("gathered twice"))
    monkeypatch.setattr(stages, "gather_safety_evidence", gather)
    monkeypatch.setattr(stages, "_registered_files", lambda _: [])
    monkeypatch.setattr(stages, "child_env", lambda *_: {})
    monkeypatch.setattr(stages, "_validate_reports", lambda _: None)
    ctx = SimpleNamespace(worktree=lambda _: Path("/virtual"), env={}, config=object())
    ticket = SimpleNamespace(stem="work", verification=[], stuck_minutes=1, frontmatter=SimpleNamespace(kind="chore"))
    result = asyncio.run(stages.gather_evidence(ctx, ticket, "ok", attempt=1, stage="merge", safety=given))
    assert gather.await_count == 0
    assert result == given


def rig(monkeypatch):
    events = []
    journal = SimpleNamespace(read=lambda: [], append=lambda typ, body, **kwargs: events.append(body))
    clock = lambda: datetime(2026, 1, 1, tzinfo=UTC)  # noqa: E731
    git = SimpleNamespace(rev_parse=AsyncMock(return_value="sha"), restore=AsyncMock(), rebase=AsyncMock(), rebase_stop_at_conflict=AsyncMock())
    driver = SimpleNamespace(clock=clock, journal=journal, redactor=SimpleNamespace(scrub=lambda s: s))
    ctx = SimpleNamespace(repo=Path("/virtual"), worktree=lambda _: Path("/virtual/work"), git=git, driver=driver, config=SimpleNamespace(review=SimpleNamespace(mechanical=[])))
    ticket = SimpleNamespace(stem="work")
    monkeypatch.setattr(stages, "ticket_change_findings", AsyncMock(return_value=[]))
    monkeypatch.setattr(merge, "main_code_unchanged", AsyncMock(return_value=False))
    monkeypatch.setattr(stages, "gather_safety_evidence", AsyncMock(return_value=evidence()))
    gather = AsyncMock(return_value=evidence())
    monkeypatch.setattr(stages, "gather_evidence", gather)
    monkeypatch.setattr(merge, "read_candidate", lambda *args: object())
    monkeypatch.setattr(stages, "check_severity", lambda *args: {})
    monkeypatch.setattr("clutch.mergequeue.run_gates", lambda *args, **kwargs: GateRunResult([]))
    monkeypatch.setattr(merge, "dirty_overlap", AsyncMock(return_value=[]))
    monkeypatch.setattr(merge, "write_squash", AsyncMock(return_value=None))
    monkeypatch.setattr(merge, "retire", AsyncMock())
    queue = MergeQueue(ctx, escalate=lambda _: None)
    return queue, ticket, events, gather


def test_inline_parameters_preserve_stage_and_suppress_facts(monkeypatch):
    queue, ticket, events, gather = rig(monkeypatch)
    result = asyncio.run(
        queue._admit(
            ticket,
            1,
            conflict_ladder=False,
            safety_tier=False,
            receipt=False,
            tree_check=False,
            red_streak=False,
            conflict_facts=False,
            inline_hosts=True,
            gather_stage="merge",
            strategy_scope=False,
            receipt_lookup=False,
        )
    )
    assert result.outcome == "ok"
    assert gather.await_args.kwargs["stage"] == "merge"
    assert not events


def test_serve_parameters_use_integration_stage_and_signal_conflict(monkeypatch):
    queue, ticket, events, gather = rig(monkeypatch)
    queue._scoped = lambda evidence, ticket: (evidence, [])
    queue.host_checks = AsyncMock(return_value=([], []))
    queue._finish = AsyncMock(return_value="finished")
    monkeypatch.setattr(stages, "served_review", AsyncMock(return_value=(None, None)))
    monkeypatch.setattr("clutch.mergequeue.Effects.run", AsyncMock(return_value={}))
    assert asyncio.run(queue._admit(ticket, 1)) == "finished"
    assert gather.await_args.kwargs["stage"] == "merge-integration"
    events.clear()
    queue.ctx.git.rebase_stop_at_conflict = AsyncMock(side_effect=GitError(["git"], 1, "", "conflict"))
    queue.ctx.git.conflicted_paths = AsyncMock(return_value=["src/a"])
    queue.ctx.git._call = AsyncMock()
    queue._resolve = AsyncMock(return_value=[Finding(code="conflict", message="conflict", paved_road="rework")])
    asyncio.run(queue._admit(ticket, 1))
    assert events[0]["kind"] == "merge_conflict_facts"
    assert events[0]["conflicted_paths"] == ["src/a"]
