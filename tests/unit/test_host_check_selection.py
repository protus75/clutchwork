# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test host check selection
# relates: [clutch/daemon.py, clutch/gates.py, clutch/mergequeue.py, clutch/stages.py]
# owner: engine
# verified: 0a308920
# hash: df63927fcfbe7450ec900da7f2e980d0b0e451ed276322e4e773ca2df864bbc5
import asyncio
import json
from datetime import datetime
from types import SimpleNamespace as NS

import pytest

from clutch import daemon, stages
from clutch.gates import GateReport
from clutch.mergequeue import MergeQueue


def entries():
    def entry(code, trigger, severity):
        return NS(code=code, trigger=trigger, severity=severity, argv=[code])

    return [entry("soft", ["src"], "soft"), entry("miss", ["other"], "hard"), entry("always", "always", "hard"), entry("path", ["src"], "hard")]


def context():
    return NS(config=NS(review=NS(mechanical=entries()), merge=NS(safety_checks=["path"])))


def test_selection_tiers():
    ctx = context()

    def selected(tier):
        return [(n, e.code) for n, e in stages.triggered_hosts(ctx, ["src/file"], tier=tier)]

    assert selected("check") == [(1, "soft"), (3, "always"), (4, "path")]
    assert selected("merge") == [(3, "always"), (4, "path")]
    assert selected("integration") == [(3, "always")]
    assert selected("safety") == [(4, "path")]
    with pytest.raises(ValueError):
        stages.triggered_hosts(ctx, [], tier="bogus")
    with pytest.raises(TypeError):
        stages.triggered_hosts(ctx, [], hard_only=True)


def test_queue_selection_and_invalid_designation(monkeypatch):
    ctx = context()
    ctx.driver = NS(redactor=NS(scrub=lambda value: value))
    queue = MergeQueue(ctx, escalate=lambda event: None)
    calls = []

    async def command(ticket, attempt, argv, code, name):
        calls.append((code, name))
        return code, GateReport(code=code, verdict="pass")

    monkeypatch.setattr(queue, "_command", command)
    results, reports = asyncio.run(queue.host_checks(None, attempt=1, safety=True))
    assert results == ["path"] and calls == [("path", "merge-safety/host-04.txt")]
    assert [r.verdict for r in reports] == ["pass"]
    calls.clear()
    results, reports = asyncio.run(queue.host_checks(None, attempt=1, safety=False))
    assert results == ["always"] and calls == [("always", "merge-integration/host-03.txt")]
    ctx.config.merge.safety_checks = ["missing"]
    calls.clear()
    results, reports = asyncio.run(queue.host_checks(None, attempt=1, safety=True))
    assert results == [] and calls == []
    assert len(reports) == 1 and reports[0].verdict == "fail"
    assert "missing" in reports[0].findings[0].message


@pytest.mark.parametrize("rc", [0, 1])
def test_invalid_coverage(tmp_path, monkeypatch, rc):
    async def execute(argv, **kwargs):
        (tmp_path / "results.json").write_text(json.dumps({"schema_version": 2, "tests": {"a": "passed"}, "seconds": {"a": 1.0}}))
        return rc, "output", ""

    monkeypatch.setattr(daemon, "storm_producer", lambda **kw: None)
    monkeypatch.setattr(daemon, "flake_detection", lambda **kw: NS(quarantine=lambda: NS(active={})))
    (tmp_path / "coverage.json").write_text("invalid")
    ctx = NS(
        worktree=lambda stem: tmp_path,
        fs=NS(remove=lambda path: path.unlink(missing_ok=True)),
        config=NS(state_dir=tmp_path, providers=[]),
        env={},
        exec_=NS(run=execute),
        driver=NS(clock=lambda: datetime(2020, 1, 1), spool=NS(write=lambda *args: None), redactor=NS(scrub=lambda value: value), journal=NS(read=lambda: [])),
    )
    entry = NS(results="results.json", coverage="coverage.json", argv=["test"], code="tests", slow_test_seconds=1.0, slow_test_limit=1)
    report = asyncio.run(stages._check_host_results(ctx, NS(stem="ticket", stuck_minutes=1), entry, 2, 1, []))
    assert report.verdict == "fail"
    findings = [f for f in report.findings if "Missing or invalid coverage report" in f.message]
    if rc == 0:
        assert len(findings) == 1 and findings[0].path == "coverage.json"
        assert "--cov-report=json:coverage.json" in findings[0].paved_road
    else:
        assert findings == []
