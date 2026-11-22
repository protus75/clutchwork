# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that Check reruns only the failed host tests with --clutch-select, marks tests that pass on rerun as flaky and releases quarantined ones, fails if the rerun exits nonzero, and reruns the full command when coverage is configured.
# relates: [clutch/config.py, clutch/daemon.py, clutch/journal.py, clutch/stages.py]
# owner: engine
# verified: fd407c31
# hash: a15144e214dd91c6ec81ca0cd19fd1a383b01b7f5dca1d03709ad5b45859187c
import asyncio
import json
from datetime import datetime
from types import SimpleNamespace as NS

from clutch import daemon, stages
from clutch.config import MechanicalCheck
from clutch.journal import EventType


def run_check(tmp_path, monkeypatch, runs, *, coverage=None, quarantine=False):
    calls, captures, selections, released, detected = [], [], [], [], []
    identity = NS(test_id="old", box_id="box")
    projection = NS(active={"box": identity} if quarantine else {}, tests={"old"} if quarantine else set(), detected={})

    def detect(**kwargs):
        detected.append(kwargs["test_id"])
        projection.tests.add(kwargs["test_id"])
        return projection

    flake = NS(quarantine=lambda: projection, detect=detect, release=lambda **kwargs: released.append(kwargs))
    box = NS(get=lambda box_id: NS(status="resolved", resolution=NS(kind="ticket", link="fix")))
    monkeypatch.setattr(daemon, "storm_producer_for_config", lambda *args, **kwargs: box)
    monkeypatch.setattr(daemon, "flake_detection", lambda **kwargs: flake)

    async def execute(argv, **kwargs):
        calls.append(list(argv))
        if "--clutch-select" in argv:
            selections.append(json.loads((tmp_path / "results.select.json").read_text()))
        rc, outcomes = runs.pop(0)
        (tmp_path / "results.json").write_text(json.dumps({"schema_version": 2, "tests": outcomes, "seconds": dict.fromkeys(outcomes, 0.0)}))
        return rc, "", ""

    events = [NS(type=EventType.STATE_TRANSITION, ticket="fix", body={"to": "merged"})]
    ctx = NS(
        worktree=lambda stem: tmp_path,
        repo=tmp_path,
        fs=NS(remove=lambda path: path.unlink(missing_ok=True), write=lambda path, data: path.write_bytes(data)),
        config=NS(providers=[]),
        env={},
        exec_=NS(run=execute),
        driver=NS(clock=lambda: datetime(2020, 1, 1), spool=NS(write=lambda stem, attempt, name, data: captures.append(name)), redactor=NS(scrub=lambda value: value), journal=NS(read=lambda: events)),
    )
    entry = MechanicalCheck(code="tests", argv=["test", "suite"], trigger="always", severity="hard", results="results.json", coverage=coverage)
    report = asyncio.run(stages._check_host_results(ctx, NS(stem="ticket", stuck_minutes=1), entry, 1, 0, []))
    return report, calls, captures, selections, released, detected


def test_selected_failure_and_capture(tmp_path, monkeypatch):
    report, calls, captures, selections, _, _ = run_check(tmp_path, monkeypatch, [(1, {"a": "failed", "b": "passed", "c": "skipped"}), (1, {"a": "failed"})])
    assert calls == [["test", "suite"], ["test", "suite", "--clutch-select", str(tmp_path / "results.select.json")]]
    assert selections == [["a"]]
    assert captures == ["check/host-01.txt", "check/host-01-rerun.txt"]
    assert any("a failed on rerun" in finding.message for finding in report.findings)


def test_passing_selected_is_flaky_and_releases_first_pass(tmp_path, monkeypatch):
    report, _, _, _, released, detected = run_check(tmp_path, monkeypatch, [(1, {"a": "failed", "old": "passed"}), (0, {"a": "passed"})], quarantine=True)
    assert report.verdict == "pass"
    assert detected == ["a"]
    assert [item["box_id"] for item in released] == ["box"]


def test_nonzero_rerun_still_fails_closed(tmp_path, monkeypatch):
    report, _, _, _, _, _ = run_check(tmp_path, monkeypatch, [(1, {"a": "failed"}), (1, {"a": "passed"}), (0, {})])
    assert report.verdict == "fail"
    assert any("exited 1" in finding.message for finding in report.findings)


def test_coverage_reruns_full_command(tmp_path, monkeypatch):
    report, calls, _, selections, _, _ = run_check(tmp_path, monkeypatch, [(1, {"a": "failed", "b": "passed"}), (1, {"a": "failed"})], coverage="coverage.json")
    assert calls == [["test", "suite"], ["test", "suite"]]
    assert selections == []
    assert any("a failed on rerun" in finding.message for finding in report.findings)
