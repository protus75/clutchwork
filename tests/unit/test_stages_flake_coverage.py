import asyncio
import json
from datetime import datetime
from types import SimpleNamespace as NS

import pytest
from pydantic import ValidationError

from clutch import daemon, stages
from clutch.config import MechanicalCheck


def test_flake_covered():
    report = {"files": {"pkg/m.py": {"executed_lines": [3]}}}
    assert stages.flake_covered(report, {"pkg/m.py": {3}}) is True
    assert stages.flake_covered(report, {"pkg/m.py": {4}}) is False
    with pytest.raises(ValueError):
        stages.flake_covered({"files": {"pkg/m.py": {}}}, {"pkg/m.py": {3}})


def test_flake_coverage_config():
    args = dict(code="u", argv=["t"], trigger="always", severity="hard", flake_coverage_argv=["t"])
    with pytest.raises(ValidationError, match="flake_coverage_argv"):
        MechanicalCheck(**args)
    assert MechanicalCheck(**args, coverage="c.json").flake_coverage_argv == ["t"]


@pytest.mark.parametrize("case", ["edited", "unset", "malformed"])
def test_check_flake_coverage(tmp_path, monkeypatch, case):
    test = "tests/test_a.py::test_x"
    calls = []

    async def execute(argv, **kwargs):
        calls.append(argv)
        if argv[0] == "flake":
            data = {"executed_lines": [3]} if case == "edited" else {}
            (tmp_path / "coverage.json").write_text(json.dumps({"files": {"pkg/m.py": data}}))
            return 1, "", ""
        outcome = "failed" if len(calls) == 1 else "passed"
        (tmp_path / "results.json").write_text(json.dumps({"schema_version": 2, "tests": {test: outcome}, "seconds": {test: 0.0}}))
        return (1 if outcome == "failed" else 0), "", ""

    async def diff(*args):
        return "diff --git a/pkg/m.py b/pkg/m.py\n--- a/pkg/m.py\n+++ b/pkg/m.py\n@@ -3 +3 @@\n-old\n+new\n"

    monkeypatch.setattr(daemon, "storm_producer", lambda **kw: None)
    monkeypatch.setattr(daemon, "flake_detection", lambda **kw: NS(quarantine=lambda: NS(active={}, tests=set())))
    ctx = NS(
        worktree=lambda stem: tmp_path,
        repo=tmp_path,
        git=NS(diff=diff),
        fs=NS(remove=lambda path: path.unlink(missing_ok=True)),
        config=NS(state_dir=tmp_path, providers=[]),
        env={},
        exec_=NS(run=execute),
        driver=NS(clock=lambda: datetime(2020, 1, 1), spool=NS(write=lambda *args: None), redactor=NS(scrub=lambda value: value), journal=NS(read=lambda: [])),
    )
    entry = MechanicalCheck(
        code="tests", argv=["test"], trigger="always", severity="hard", results="results.json", coverage="coverage.json", **({} if case == "unset" else {"flake_coverage_argv": ["flake"]})
    )
    report = asyncio.run(stages._check_host_results(ctx, NS(stem="ticket", stuck_minutes=1), entry, 2, 1, ["pkg/m.py"]))
    assert report.verdict == "fail"
    if case == "edited":
        assert any(test in finding.message for finding in report.findings)
    else:
        assert any("flake_coverage_argv" in finding.paved_road for finding in report.findings)
    assert calls == ([["test"], ["test"]] if case == "unset" else [["test"], ["test"], ["flake", test]])
